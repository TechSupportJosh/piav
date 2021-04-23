import axios from "axios";
import { Executable } from "../models/types/Executable";
import { QueueEntry } from "../models/types/Queue";
import { TaskInput } from "../models/types/TaskInput";
import { TaskOutput } from "../models/types/TaskOutput";

export const API_BASE = "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE + "/portal",
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

const getExecutables = async () => {
  const response = await client.get<Executable[]>("/executable");

  if (response.status === 200) return response.data;
};

const setupExecutable = async (applicationName: string, fullInstallationName: string, installer: string, installerName: string) => {
  const response = await client.post(`/executable`, {
    application_name: applicationName,
    full_installation_name: fullInstallationName,
    installer: installer,
    installer_name: installerName,
  });

  return response.status === 201;
};

export default {
  getQueuedMachines,
  getTaskInput,
  getTaskOutput,
  getExecutables,
  setupExecutable,
};
