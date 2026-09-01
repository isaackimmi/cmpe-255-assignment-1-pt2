import { useMemo, useState } from "react";
import { Button } from "../ui/Button";
import { TaskForm } from "./TaskForm";
import { TaskRow } from "./TaskRow";

const filters = [
  { id: "all", label: "All", matches: () => true },
  { id: "todo", label: "To do", matches: (task) => !task.done },
  { id: "done", label: "Done", matches: (task) => task.done },
];

export function TaskBoard({ tasks, pending, busy, onCreate, onToggle, onDelete }) {
  const [activeFilter, setActiveFilter] = useState("all");
  const [query, setQuery] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const visibleTasks = useMemo(() => {
    const filter = filters.find(({ id }) => id === activeFilter) || filters[0];
    const normalizedQuery = query.trim().toLowerCase();
    return tasks.filter((task) => filter.matches(task) && `${task.title} ${task.area}`.toLowerCase().includes(normalizedQuery));
  }, [tasks, activeFilter, query]);

  const counts = { all: tasks.length, todo: tasks.filter((task) => !task.done).length, done: tasks.filter((task) => task.done).length };
  return (
    <article className="panel tasks">
      <div className="section-head">
        <div><h2>Work queue</h2><p>CRUD state is served by FastAPI.</p></div>
        <Button variant="ghost" aria-controls="task-form" aria-expanded={formOpen} onClick={() => setFormOpen((open) => !open)}>＋ Add task</Button>
      </div>
      <div className="toolbar">
        {filters.map((filter) => (
          <button key={filter.id} className={`filter ${activeFilter === filter.id ? "active" : ""}`} type="button" aria-pressed={activeFilter === filter.id} onClick={() => setActiveFilter(filter.id)}>
            {filter.label} {counts[filter.id]}
          </button>
        ))}
        <label className="search"><span className="sr-only">Search tasks</span><input type="search" placeholder="Search tasks" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
      </div>
      <div className="task-list" aria-live="polite">
        {visibleTasks.length ? visibleTasks.map((task) => <TaskRow key={task.id} task={task} pending={pending} busy={busy} onToggle={onToggle} onDelete={onDelete} />) : <p className="muted">No tasks match this filter.</p>}
      </div>
      {formOpen ? <div id="task-form"><TaskForm busy={busy} onSubmit={onCreate} /></div> : null}
    </article>
  );
}
