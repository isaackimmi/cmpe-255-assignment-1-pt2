import { useState } from "react";
import { Button } from "../ui/Button";

export function TaskForm({ busy, onSubmit }) {
  const [title, setTitle] = useState("");
  const [priority, setPriority] = useState("medium");

  async function handleSubmit(event) {
    event.preventDefault();
    const result = await onSubmit({ title, priority });
    if (result.ok) {
      setTitle("");
      setPriority("medium");
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <label className="sr-only" htmlFor="task-title">Task title</label>
      <input id="task-title" maxLength="120" required placeholder="e.g. Check holiday seasonality" value={title} onChange={(event) => setTitle(event.target.value)} />
      <label className="sr-only" htmlFor="task-priority">Priority</label>
      <select id="task-priority" value={priority} onChange={(event) => setPriority(event.target.value)}>
        <option value="high">high</option><option value="medium">medium</option><option value="low">low</option>
      </select>
      <Button type="submit" disabled={busy}>Add</Button>
    </form>
  );
}
