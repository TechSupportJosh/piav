export interface Reference {
  auto_id: string;
}

export interface UIControl {
  reference: Reference;
  meta: Record<string, any>;
  type: string;
}

export interface Action {
  control: UIControl;
  wait_for_element_timeout: number;
  delay_after_action: number;
  method: string;
  method_params: Record<string, any>;
}

export interface TaskInput {
  _id: string;
  status: string;
  executable_id: string;
  parent_task: string;
  setup_actions: Action[];
  actions: Action[];
}
