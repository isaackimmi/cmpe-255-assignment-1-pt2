import { AppShell } from "./components/layout/AppShell";
import { DashboardHeader } from "./components/layout/DashboardHeader";
import { MetricGrid } from "./components/project/MetricGrid";
import { ProjectContext } from "./components/project/ProjectContext";
import { StatusMessage } from "./components/feedback/StatusMessage";
import { TaskBoard } from "./components/tasks/TaskBoard";
import { WorkflowPanel } from "./components/workflow/WorkflowPanel";
import { WorkspaceError } from "./components/feedback/WorkspaceError";
import { presentation } from "./config/presentation";
import { useWorkspace } from "./hooks/useWorkspace";

export function App() {
  const workspaceState = useWorkspace();
  const { workspace, loading, error } = workspaceState;

  if (loading) return <div className="loading" role="status" aria-live="polite">Loading workspace…</div>;
  if (error || !workspace) return <WorkspaceError error={error} />;

  const completedTasks = workspace.tasks.filter((task) => task.done).length;
  const completedStages = workspace.workflow.stages.filter((stage) => stage.status === "complete").length;

  return (
    <AppShell workspace={workspace} profile={presentation.profile}>
      <DashboardHeader
        project={workspace.project}
        content={presentation.hero}
        busy={workspaceState.busy}
        checking={workspaceState.pending === "agent"}
        onAgentCheck={workspaceState.runAgentCheck}
      />
      <StatusMessage message={workspaceState.statusMessage} />
      <ProjectContext project={workspace.project} readiness={workspace.readiness} />
      <MetricGrid
        completedTasks={completedTasks}
        taskCount={workspace.tasks.length}
        completedStages={completedStages}
        stageCount={workspace.workflow.stages.length}
      />
      <section className="content-grid" aria-label="Workspace details">
        <TaskBoard
          tasks={workspace.tasks}
          pending={workspaceState.pending}
          busy={workspaceState.busy}
          onCreate={workspaceState.createTask}
          onToggle={workspaceState.toggleTask}
          onDelete={workspaceState.deleteTask}
        />
        <WorkflowPanel workflow={workspace.workflow} />
      </section>
      <div className="footer">Local E2E workspace · {workspace.readiness.boundary}</div>
    </AppShell>
  );
}
