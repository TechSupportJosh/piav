export interface QueueEntry {
  _id: string;
  status: "waiting" | "started" | "finished";
}
