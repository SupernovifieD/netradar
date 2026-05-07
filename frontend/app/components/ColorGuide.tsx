export default function ColorGuide({ className = "" }: { className?: string }) {
  return (
    <div className={className}>
      Color guide:
      <div>🟢 Service is available</div>
      <div>🔵 Service is available, but ping data is missing</div>
      <div>🟡 Service is unstable</div>
      <div>🔴 Service outage</div>
    </div>
  );
}
