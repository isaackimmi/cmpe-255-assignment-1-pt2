import * as Progress from "@radix-ui/react-progress";
import { Card } from "../ui/Card";

function ProjectBriefCard({ project }) {
  return (
    <Card>
      <div className="card-top"><p className="eyebrow">Project brief</p><span className="status">Demo plan</span></div>
      <h2>{project.brief}</h2>
      <p>{project.goal}</p>
      <p className="muted">Owner · Alex Kim · Local example workspace</p>
    </Card>
  );
}

function ReadinessCard({ readiness }) {
  return (
    <Card>
      <div className="card-top"><p className="eyebrow">Dataset readiness</p><span className="status">{readiness.status}</span></div>
      <h2>{readiness.dataset}</h2>
      <p>{readiness.note}</p>
      <div className="quality">
        <span>Readiness</span>
        <Progress.Root className="progress-root" value={readiness.score} aria-label="Dataset readiness">
          <Progress.Indicator className="progress-indicator" style={{ transform: `translateX(-${100 - readiness.score}%)` }} />
        </Progress.Root>
        <strong>{readiness.score}%</strong>
      </div>
    </Card>
  );
}

export function ProjectContext({ project, readiness }) {
  return <section className="context-grid" aria-label="Project context"><ProjectBriefCard project={project} /><ReadinessCard readiness={readiness} /></section>;
}
