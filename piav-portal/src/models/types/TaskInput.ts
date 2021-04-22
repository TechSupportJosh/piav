export interface Reference {
  auto_id: string;
}

export interface Precursor {
  reference: Reference;
  wait_for_element_timeout: number;
  delay_after_action: number;
  action: {
    method: string;
    parameters: Record<string, any>;
  };
}

export interface TaskInput {
  precursors: Precursor[];
}
