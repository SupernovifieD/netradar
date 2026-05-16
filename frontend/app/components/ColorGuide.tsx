import { statusTimelineConfig } from "@/lib/config";

export default function ColorGuide({ className = "" }: { className?: string }) {
  return (
    <div className={className}>
      Color guide:
      <div>🟢 {statusTimelineConfig.tokens.green.label}</div>
      <div>🟢 {statusTimelineConfig.tokens.darkgreen.label}</div>
      <div>🟡 {statusTimelineConfig.tokens.orange.label}</div>
      <div>🔵 {statusTimelineConfig.tokens.blue.label}</div>
      <div>🔵 {statusTimelineConfig.tokens.darkblue.label}</div>
      <div>🔴 {statusTimelineConfig.tokens.red.label}</div>
      <div>⚪ {statusTimelineConfig.tokens.grey.label}</div>
    </div>
  );
}
