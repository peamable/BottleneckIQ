#!/usr/bin/env python3
"""
Bottleneck Pattern Detection Script

This script analyzes temporal patterns in bottleneck occurrences to identify
when bottlenecks are most likely to happen and provides recommendations
for resource allocation and process improvements.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set up plotting
sns.set(style='whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)

def load_and_prepare_data(data_path):
    """Load and prepare the dataset for analysis."""
    print(f"Loading data from {data_path}...")

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} records with {len(df.columns)} columns")

    # Detect timestamp column
    timestamp_col = 'timestamp' if 'timestamp' in df.columns else 'timestamps' if 'timestamps' in df.columns else None
    if timestamp_col is None or 'stay_id' not in df.columns:
        raise ValueError('Data must have stay_id and a timestamp/timestamps column')

    # Convert timestamp
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')
    if timestamp_col != 'timestamp':
        df['timestamp'] = df[timestamp_col]

    # Add temporal features first
    df['hour_of_day'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['month'] = df['timestamp'].dt.month
    df['day_name'] = df['timestamp'].dt.day_name()
    df['time_of_day'] = pd.cut(df['hour_of_day'],
                               bins=[0, 6, 12, 18, 24],
                               labels=['Night', 'Morning', 'Afternoon', 'Evening'],
                               right=False)

    # Compute bottleneck labels from event-level data if activity column present
    if 'activity' in df.columns:
        df = _compute_bottleneck_labels(df)

    return df


def _compute_bottleneck_labels(df):
    """Compute per-stay bottleneck labels from event-level data (vectorized)."""
    activity_map = {
        'enter the ed': 'entry',
        'triage in the ed': 'triage',
        'vital sign check': 'vital',
        'medicine reconciliation': 'medrecon',
        'medicine dispensations': 'dispen',
        'discharge from the ed': 'discharge'
    }
    df = df.copy()
    df['_activity'] = df['activity'].astype(str).str.strip().str.lower().replace(activity_map)
    df['stay_id'] = pd.to_numeric(df['stay_id'], errors='coerce')
    df = df.sort_values(['stay_id', 'timestamp'])

    # Vectorized delta calculation
    df['_prev_ts'] = df.groupby('stay_id')['timestamp'].shift(1)
    df['_delta_min'] = (df['timestamp'] - df['_prev_ts']).dt.total_seconds() / 60.0

    stages = ['vital', 'medrecon', 'dispen', 'discharge']
    timing_rows = df[df['_activity'].isin(stages)][['stay_id', '_activity', '_delta_min']].dropna()
    timing_rows = timing_rows.drop_duplicates(['stay_id', '_activity'])
    timing_pivot = timing_rows.pivot(index='stay_id', columns='_activity', values='_delta_min')
    timing_pivot.columns = [f'time_to_{c}' for c in timing_pivot.columns]
    timing_pivot = timing_pivot.reset_index()

    for stage in stages:
        col = f'time_to_{stage}'
        if col in timing_pivot.columns:
            p90 = timing_pivot[col].dropna().quantile(0.90)
            timing_pivot[f'is_bottleneck_{stage}'] = ((timing_pivot[col] > p90) & timing_pivot[col].notna()).astype(int)
        else:
            timing_pivot[f'is_bottleneck_{stage}'] = 0

    timing_pivot['is_bottleneck'] = timing_pivot[[f'is_bottleneck_{s}' for s in stages]].max(axis=1).astype(int)

    first_per_stay = df.drop_duplicates('stay_id')[['stay_id', 'timestamp', 'hour_of_day', 'day_of_week', 'is_weekend', 'month', 'day_name', 'time_of_day']]
    merged = first_per_stay.merge(timing_pivot[['stay_id', 'is_bottleneck']], on='stay_id', how='left')
    merged['is_bottleneck'] = merged['is_bottleneck'].fillna(0).astype(int)
    return merged


def compute_bottleneck_patterns(df):
    """Compute bottleneck patterns across different temporal dimensions."""
    print("\nComputing bottleneck patterns...")

    patterns = {}

    # Overall bottleneck rate
    total_bottlenecks = df['is_bottleneck'].sum()
    total_records = len(df)
    overall_rate = total_bottlenecks / total_records
    patterns['overall_rate'] = overall_rate
    print(f"Overall bottleneck rate: {overall_rate:.3f}")

    # By hour of day
    hourly_patterns = df.groupby('hour_of_day')['is_bottleneck'].agg(['count', 'sum', 'mean'])
    hourly_patterns.columns = ['total_visits', 'bottleneck_count', 'bottleneck_rate']
    patterns['hourly'] = hourly_patterns

    # By day of week
    daily_patterns = df.groupby('day_of_week')['is_bottleneck'].agg(['count', 'sum', 'mean'])
    daily_patterns.columns = ['total_visits', 'bottleneck_count', 'bottleneck_rate']
    daily_patterns.index = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    patterns['daily'] = daily_patterns

    # By time of day category
    time_patterns = df.groupby('time_of_day')['is_bottleneck'].agg(['count', 'sum', 'mean'])
    time_patterns.columns = ['total_visits', 'bottleneck_count', 'bottleneck_rate']
    patterns['time_of_day'] = time_patterns

    # Weekend vs Weekday
    weekend_patterns = df.groupby('is_weekend')['is_bottleneck'].agg(['count', 'sum', 'mean'])
    weekend_patterns.columns = ['total_visits', 'bottleneck_count', 'bottleneck_rate']
    weekend_patterns.index = ['Weekday', 'Weekend']
    patterns['weekend'] = weekend_patterns

    # Peak hours analysis (top 3 bottleneck hours)
    top_hours = hourly_patterns.nlargest(3, 'bottleneck_rate')
    patterns['peak_hours'] = top_hours

    # Peak days analysis
    top_days = daily_patterns.nlargest(3, 'bottleneck_rate')
    patterns['peak_days'] = top_days

    return patterns

def generate_recommendations(patterns):
    """Generate actionable recommendations based on patterns."""
    print("\nGenerating recommendations...")

    recommendations = []

    # Overall assessment
    overall_rate = patterns['overall_rate']
    if overall_rate > 0.3:
        recommendations.append("HIGH BOTTLENECK RISK: Overall bottleneck rate is high. Consider systemic improvements.")
    elif overall_rate > 0.2:
        recommendations.append("MODERATE BOTTLENECK RISK: Monitor closely and implement targeted interventions.")
    else:
        recommendations.append("LOW BOTTLENECK RISK: Current processes are generally effective.")

    # Time-based recommendations
    hourly = patterns['hourly']
    peak_hours = patterns['peak_hours']

    for hour, row in peak_hours.iterrows():
        rate = row['bottleneck_rate']
        count = row['bottleneck_count']
        if rate > overall_rate * 1.5:  # Significantly higher than average
            time_label = f"{hour}:00-{hour+1}:00"
            recommendations.append(f"PEAK HOUR ALERT: {time_label} shows {rate:.1%} bottleneck rate ({count} cases). Increase staffing during this hour.")

    # Day-based recommendations
    daily = patterns['daily']
    peak_days = patterns['peak_days']

    for day, row in peak_days.iterrows():
        rate = row['bottleneck_rate']
        count = row['bottleneck_count']
        if rate > overall_rate * 1.5:
            recommendations.append(f"PEAK DAY ALERT: {day}s show {rate:.1%} bottleneck rate ({count} cases). Prepare additional resources on {day}s.")

    # Weekend analysis
    weekend = patterns['weekend']
    weekend_rate = weekend.loc['Weekend', 'bottleneck_rate']
    weekday_rate = weekend.loc['Weekday', 'bottleneck_rate']

    if weekend_rate > weekday_rate * 1.2:
        recommendations.append(f"WEEKEND RISK: Weekend bottleneck rate ({weekend_rate:.1%}) is higher than weekdays ({weekday_rate:.1%}). Ensure adequate weekend staffing.")

    # Time of day analysis
    time_of_day = patterns['time_of_day']
    peak_time = time_of_day['bottleneck_rate'].idxmax()
    peak_time_rate = time_of_day['bottleneck_rate'].max()

    if peak_time_rate > overall_rate * 1.5:
        recommendations.append(f"PEAK TIME ALERT: {peak_time} shows highest bottleneck risk ({peak_time_rate:.1%}). Focus monitoring during {peak_time.lower()} hours.")

    return recommendations

def create_visualizations(patterns, output_dir):
    """Create and save visualizations of bottleneck patterns."""
    print("\nCreating visualizations...")

    output_dir.mkdir(exist_ok=True)

    # Hourly bottleneck rates
    plt.figure(figsize=(12, 6))
    hourly = patterns['hourly']
    plt.bar(hourly.index, hourly['bottleneck_rate'] * 100, alpha=0.7, color='skyblue')
    plt.axhline(y=patterns['overall_rate'] * 100, color='red', linestyle='--', label=f"Avg {patterns['overall_rate']*100:.1f}%")
    plt.xlabel('Hour of Day')
    plt.ylabel('Bottleneck Rate (%)')
    plt.title('Bottleneck Rates by Hour of Day')
    plt.legend()
    plt.xticks(range(0, 24))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'bottleneck_by_hour.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Daily bottleneck rates
    plt.figure(figsize=(10, 6))
    daily = patterns['daily']
    bars = plt.bar(daily.index, daily['bottleneck_rate'] * 100, alpha=0.7, color='lightcoral')
    plt.axhline(y=patterns['overall_rate'] * 100, color='red', linestyle='--', label=f"Avg {patterns['overall_rate']*100:.1f}%")
    plt.xlabel('Day of Week')
    plt.ylabel('Bottleneck Rate (%)')
    plt.title('Bottleneck Rates by Day of Week')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)

    # Add value labels on bars
    for bar, rate in zip(bars, daily['bottleneck_rate']):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f'{rate*100:.1f}%', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'bottleneck_by_day.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Time of day categories
    plt.figure(figsize=(8, 6))
    time_of_day = patterns['time_of_day']
    bars = plt.bar(time_of_day.index, time_of_day['bottleneck_rate'] * 100, alpha=0.7, color='lightgreen')
    plt.axhline(y=patterns['overall_rate'] * 100, color='red', linestyle='--', label=f"Avg {patterns['overall_rate']*100:.1f}%")
    plt.xlabel('Time of Day')
    plt.ylabel('Bottleneck Rate (%)')
    plt.title('Bottleneck Rates by Time of Day')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Add value labels
    for bar, rate in zip(bars, time_of_day['bottleneck_rate']):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                f'{rate*100:.1f}%', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'bottleneck_by_time_of_day.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Visualizations saved to {output_dir}")

def main():
    """Main execution function."""
    print("=== Bottleneck Pattern Detection Analysis ===\n")

    # Configuration
    data_dir = Path('.')
    data_file = data_dir / 'data_MIMIC.csv'  # Adjust path as needed
    output_dir = data_dir / 'bottleneck_analysis'

    try:
        # Load and prepare data
        df = load_and_prepare_data(data_file)

        # Compute patterns
        patterns = compute_bottleneck_patterns(df)

        # Generate recommendations
        recommendations = generate_recommendations(patterns)

        # Create visualizations
        create_visualizations(patterns, output_dir)

        # Print summary report
        print("\n" + "="*60)
        print("BOTTLENECK PATTERN ANALYSIS REPORT")
        print("="*60)

        print(f"Overall Bottleneck Rate: {patterns['overall_rate']:.1%}")
        print(f"Total Records Analyzed: {len(df):,}")
        print(f"Total Bottlenecks: {int(df['is_bottleneck'].sum()):,}")

        print("\nTOP BOTTLENECK HOURS:")
        print("-" * 30)
        peak_hours = patterns['peak_hours']
        for hour, row in peak_hours.iterrows():
            print(f"  {int(hour):02d}:00 -- {row['bottleneck_rate']:.1%} rate ({int(row['bottleneck_count'])} cases)")

        print("\nTOP BOTTLENECK DAYS:")
        print("-" * 30)
        peak_days = patterns['peak_days']
        for day, row in peak_days.iterrows():
            print(f"  {day:<12} -- {row['bottleneck_rate']:.1%} rate ({int(row['bottleneck_count'])} cases)")

        print("\nRECOMMENDATIONS:")
        print("-" * 30)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

        print(f"\nVisualizations saved to: {output_dir}/")
        print("Files: bottleneck_by_hour.png, bottleneck_by_day.png, bottleneck_by_time_of_day.png")

    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1

    print("\nAnalysis completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main())