from sqlalchemy import text

from app.core.database import engine


def _issue(code: str, message: str, count: int, skippable: bool) -> dict:
    return {
        "code": code,
        "message": message,
        "count": int(count),
        "skippable": skippable,
    }


def _format_count(count: int, singular: str, plural: str | None = None) -> str:
    plural = plural or f"{singular}s"
    return f"{count} {singular if count == 1 else plural}"


def validate_batch(batch_id: str) -> list[dict]:
    """
    Returns structured validation issues for the staged batch.
    Empty list = pass.
    """
    issues = []

    with engine.begin() as conn:
        bad_ed = conn.execute(text("""
            SELECT COUNT(*) FROM ed_stay_staging
            WHERE batch_id = :b
              AND (stay_id IS NULL OR ed_timestamp IS NULL OR activity IS NULL OR activity = '')
        """), {"b": batch_id}).scalar() or 0
        if bad_ed > 0:
            issues.append(_issue(
                "ed_missing_required",
                f"{_format_count(bad_ed, 'row')} {'is' if bad_ed == 1 else 'are'} missing stay_id, ed_timestamp, or activity.",
                bad_ed,
                True,
            ))

        repeated_rows_in_batch = conn.execute(text("""
            SELECT COUNT(*) FROM (
              SELECT stay_id, activity, ed_timestamp, COUNT(*) c
              FROM ed_stay_staging
              WHERE batch_id = :b
              GROUP BY stay_id, activity, ed_timestamp
              HAVING c > 1
            ) t
        """), {"b": batch_id}).scalar() or 0
        if repeated_rows_in_batch > 0:
            issues.append(_issue(
                "ed_duplicate_events",
                f"{_format_count(repeated_rows_in_batch, 'duplicate event key')} {'was' if repeated_rows_in_batch == 1 else 'were'} found in the staged ED events.",
                repeated_rows_in_batch,
                False,
            ))

        bad_stay_info_nulls = conn.execute(text("""
            SELECT COUNT(*) FROM stay_info_staging
            WHERE batch_id = :b
              AND (
                gender IS NULL
                OR race IS NULL
                OR arrival_transport IS NULL
                OR disposition IS NULL
                OR chiefcomplaint IS NULL
              )
        """), {"b": batch_id}).scalar() or 0
        if bad_stay_info_nulls > 0:
            issues.append(_issue(
                "stay_info_missing_required",
                f"{_format_count(bad_stay_info_nulls, 'stay record')} {'is' if bad_stay_info_nulls == 1 else 'are'} missing gender, race, arrival transport, disposition, or chief complaint.",
                bad_stay_info_nulls,
                True,
            ))

        bad_scale_level = conn.execute(text("""
            SELECT COUNT(*) FROM stay_info_staging
            WHERE batch_id = :b
              AND (scale_level IS NULL OR scale_level < 1 OR scale_level > 5 OR scale_level <> FLOOR(scale_level))
        """), {"b": batch_id}).scalar() or 0
        if bad_scale_level > 0:
            issues.append(_issue(
                "stay_info_invalid_scale_level",
                f"{_format_count(bad_scale_level, 'stay record')} {'has' if bad_scale_level == 1 else 'have'} an invalid acuity value; expected whole numbers from 1 to 5.",
                bad_scale_level,
                True,
            ))

        unmatched_ed_stays = conn.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT e.stay_id
                FROM ed_stay_staging e
                WHERE e.batch_id = :b
                  AND e.stay_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1
                      FROM stay_info_staging s
                      WHERE s.batch_id = :b
                        AND s.stay_id = e.stay_id
                  )
            ) unmatched
        """), {"b": batch_id}).scalar() or 0
        if unmatched_ed_stays > 0:
            issues.append(_issue(
                "ed_missing_matching_stay_info",
                f"{_format_count(unmatched_ed_stays, 'stay_id')} {'has' if unmatched_ed_stays == 1 else 'have'} no matching stay information. Please check fields such as gender, race, arrival transport, disposition, chief complaint, or acuity.",
                unmatched_ed_stays,
                True,
            ))

    return issues


def delete_skippable_rows(batch_id: str, issues: list[dict]) -> list[dict]:
    """
    Deletes staging rows for the skippable validation issues that were detected.
    Returns a summary of the cleanup actions taken.
    """
    skipped = []
    issue_codes = {issue["code"] for issue in issues if issue.get("skippable")}

    with engine.begin() as conn:
        if "ed_missing_required" in issue_codes:
            deleted = conn.execute(text("""
                DELETE FROM ed_stay_staging
                WHERE batch_id = :b
                  AND (stay_id IS NULL OR ed_timestamp IS NULL OR activity IS NULL OR activity = '')
            """), {"b": batch_id}).rowcount
            if deleted:
                skipped.append({"code": "ed_missing_required", "rows_deleted": int(deleted)})

        if "stay_info_missing_required" in issue_codes:
            deleted = conn.execute(text("""
                DELETE FROM stay_info_staging
                WHERE batch_id = :b
                  AND (
                    gender IS NULL
                    OR race IS NULL
                    OR arrival_transport IS NULL
                    OR disposition IS NULL
                    OR chiefcomplaint IS NULL
                  )
            """), {"b": batch_id}).rowcount
            if deleted:
                skipped.append({"code": "stay_info_missing_required", "rows_deleted": int(deleted)})

        if "stay_info_invalid_scale_level" in issue_codes:
            deleted = conn.execute(text("""
                DELETE FROM stay_info_staging
                WHERE batch_id = :b
                  AND (scale_level IS NULL OR scale_level < 1 OR scale_level > 5 OR scale_level <> FLOOR(scale_level))
            """), {"b": batch_id}).rowcount
            if deleted:
                skipped.append({"code": "stay_info_invalid_scale_level", "rows_deleted": int(deleted)})

        if "ed_missing_matching_stay_info" in issue_codes:
            deleted = conn.execute(text("""
                DELETE e
                FROM ed_stay_staging e
                LEFT JOIN stay_info_staging s
                  ON s.batch_id = e.batch_id
                 AND s.stay_id = e.stay_id
                WHERE e.batch_id = :b
                  AND e.stay_id IS NOT NULL
                  AND s.stay_id IS NULL
            """), {"b": batch_id}).rowcount
            if deleted:
                skipped.append({"code": "ed_missing_matching_stay_info", "rows_deleted": int(deleted)})

    return skipped
