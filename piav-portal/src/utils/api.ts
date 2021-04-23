import axios from "axios";
import { QueueEntry } from "../models/types/Queue";
import { TaskInput } from "../models/types/TaskInput";
import { TaskOutput } from "../models/types/TaskOutput";

const client = axios.create({
  baseURL: "http://localhost:8000/portal",
  validateStatus: undefined,
});

const getQueuedMachines = async () => {
  const response = await client.get<QueueEntry[]>("/queue");

  if (response.status === 200) return response.data;
};

const getTaskInput = async (taskId: string) => {
  const response = await client.get<TaskInput>(`/task/${taskId}/input`);

  if (response.status === 200) return response.data;
};

const getTaskOutput = async (taskId: string) => {
  const response = await client.get<TaskOutput>(`/task/${taskId}/output`);

  if (response.status === 200) return response.data;
};

export default {
  getQueuedMachines,
  getTaskInput,
  getTaskOutput,
};
