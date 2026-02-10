import EmptyMetricsState from "../components/empty_metrics_state";



// const ViewMetricsPage = () => {
//   // TEST: Change this to 'true' to see your charts, 'false' to see the Empty State
//   const has_data = false; 

//   if (!has_data) {
//     return <EmptyMetricsState />;
//   }

//   return (
//     <div className="metrics_dashboard">
//       <BottleneckBanner stage_name="Triage" />
//       {/* Your charts go here */}
//     </div>
//   );
// };

const ViewMetricsPage = () => {
  const has_data = false;

  return (
    <div className="view_metrics_page_wrapper"> 
      <div className="metrics_content_container">
        {!has_data ? (
          <EmptyMetricsState />  /* The message lives inside here! */
        ) : (
          <div>Charts will go here</div>
        )}
      </div>
    </div>
  );
};

export default ViewMetricsPage