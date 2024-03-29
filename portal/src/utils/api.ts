import axios from "axios";
import { Error } from "../models/types/Error";
import { Executable } from "../models/types/Executable";
import { TaskInput } from "../models/types/TaskInput";
import { TaskOutput } from "../models/types/TaskOutput";

export const API_BASE = "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE + "/",
  validateStatus: undefined,
});

const getTaskInputs = async () => {
  const response = await client.get<TaskInput[]>(`/task/input`);

  if (response.status === 200) return response.data;
};

const getTaskInput = async (taskId: string) => {
  const response = await client.get<TaskInput>(`/task/input/${taskId}`);

  if (response.status === 200) return response.data;
};

const getTaskOutput = async (taskId: string) => {
  const response = await client.get<TaskOutput>(`/task/output/${taskId}`);

  if (response.status === 200) return response.data;
};

const getTaskOutputs = async (windowEnumeration = true, kernelEvents = true) => {
  const response = await client.get<TaskOutput[]>(`/task/output`, {
    params: { window_enumeration: windowEnumeration, kernel_events: kernelEvents },
  });

  if (response.status === 200) return response.data;
};

const getExecutables = async () => {
  const response = await client.get<Executable[]>("/executable/");

  if (response.status === 200) return response.data;
};

const setupExecutable = async (applicationName: string, fullInstallationName: string, installer: string, installerName: string) => {
  const response = await client.post(`/executable/`, {
    application_name: applicationName,
    full_installation_name: fullInstallationName,
    installer: installer,
    installer_name: installerName,
  });

  return response.status === 201;
};

const getErrors = async () => {
  const response = await client.get<Error[]>(`/error/`);

  if (response.status === 200) return response.data;
};

const getError = async (taskId: string) => {
  const response = await client.get<Error[]>(`/error/${taskId}`);

  if (response.status === 200) return response.data;
};

const restartTask = async (taskId: string) => {
  const response = await client.post(`/task/restart/${taskId}`);

  return response.status === 200;
};

export default {
  getTaskInput,
  getTaskInputs,
  getTaskOutput,
  getTaskOutputs,
  getExecutables,
  setupExecutable,
  getErrors,
  getError,
  restartTask,
};
