import * as Checkbox from "@radix-ui/react-checkbox";

export function TaskRow({ task, pending, busy, onToggle, onDelete }) {
  const deleting = pending === `delete-${task.id}`;
  return (
    <div className={`task ${task.done ? "done" : ""}`}>
      <Checkbox.Root
        className="task-checkbox"
        checked={task.done}
        disabled={busy}
        onCheckedChange={(checked) => onToggle(task.id, checked === true)}
        aria-label={`Complete ${task.title}`}
      >
        <Checkbox.Indicator>✓</Checkbox.Indicator>
      </Checkbox.Root>
      <span className="task-label">{task.title}<span className="muted"> · {task.area}</span></span>
      <span className="priority">{task.priority}</span>
      <button className="delete" type="button" disabled={busy} onClick={() => onDelete(task.id)} aria-label={`Delete ${task.title}`}>
        {deleting ? "…" : "×"}
      </button>
    </div>
  );
}
