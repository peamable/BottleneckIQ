import React from 'react';
import { AlertTriangle, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import '../bottleneck_banner.css';

const formatStageName = (stageName = '') =>
  stageName.replace(/^time_to_/, '').replace(/_/g, ' ').toUpperCase();

const formatStageList = (stages = []) => {
  const names = stages.map((stage) => formatStageName(stage.stage));

  if (names.length === 0) return '';
  if (names.length === 1) return names[0];
  if (names.length === 2) return `${names[0]} AND ${names[1]}`;

  return `${names.slice(0, -1).join(', ')}, AND ${names[names.length - 1]}`;
};

const BottleneckBanner = ({ summary, uploadId }) => {
  const navigate = useNavigate();
  const bottleneckStages = summary?.stages?.filter((stage) => stage.status === 'Bottleneck') || [];
  const needsImprovementStages =
    summary?.stages?.filter((stage) => stage.status === 'Needs Improvement') || [];
  const primaryStage = bottleneckStages[0]
    || needsImprovementStages[0]
    || summary?.stages?.[0];

  const overallStatus = summary?.overall_status || 'No Data';
  const isBottleneck = overallStatus === 'Bottleneck';
  const isNeedsImprovement = overallStatus === 'Needs Improvement';

  let label = 'System Status';
  let headline = 'No bottleneck data available';
  let toneClass = 'banner_neutral';

  if (isBottleneck && primaryStage) {
    label = 'BOTTLENECK DETECTED';
    headline = `HIGH LATENCY IN ${formatStageList(bottleneckStages)}`;
    toneClass = 'banner_danger';
  } else if (isNeedsImprovement && primaryStage) {
    label = 'NEEDS IMPROVEMENT';
    headline = `Latency rising in ${formatStageList(needsImprovementStages)}`;
    toneClass = 'banner_warning';
  } else if (overallStatus === 'Normal') {
    label = 'FLOW STABLE';
    headline = 'All monitored stages are within normal thresholds';
    toneClass = 'banner_success';
  } else if (summary?.banner_message) {
    headline = summary.banner_message;
  }

  const navigateToInsights = () => {
    const target = uploadId ? `/insights?upload_id=${uploadId}` : '/insights';
    navigate(target, uploadId ? { state: { upload_id: uploadId } } : undefined);
  };

  if (!isBottleneck && !isNeedsImprovement) {
    return (
      <div className="banner_button_only">
        <button
          className="banner_action_btn banner_action_btn_blue"
          onClick={navigateToInsights}
        > Insights<ChevronRight size={18} /></button>
      </div>
    );
  }

  return (
    <div className={`bottleneck_banner ${toneClass}`}>
      <div className="banner_left_content">
        <div className="alert_icon_container">
          <AlertTriangle size={24} fill="#fbbf24" color="#1e293b" />
        </div>
        <div className="banner_text_stack">
          <span className="banner_label">{label}</span>
          <h3 className="banner_main_text">
            {isBottleneck && bottleneckStages.length > 0 ? (
              <>
                HIGH LATENCY IN <span className="stage_highlight">{formatStageList(bottleneckStages)}</span>
              </>
            ) : isNeedsImprovement && needsImprovementStages.length > 0 ? (
              <>
                Latency rising in <span className="stage_highlight">{formatStageList(needsImprovementStages)}</span>
              </>
            ) : (
              headline
            )}
          </h3>
          {summary?.banner_message && (
            <p className="banner_subtext">{summary.banner_message}</p>
          )}
        </div>
      </div>

      <button 
        className="banner_action_btn" 
        onClick={navigateToInsights}
      > Insights<ChevronRight size={18} /></button>
    </div>
  );
};

export default BottleneckBanner;
