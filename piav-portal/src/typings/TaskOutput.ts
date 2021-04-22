export interface KernelEvent {
  event_name: string;
  params: Record<string, any>;
}

export interface TaskOutput {
  window_enumeration: {
    application_alive: boolean;
    program_installed: boolean;
    top_window_texts: string[];
    found_controls: {
      control_type: string;
      reference: {
        auto_id: string;
      };
      _debug: Record<string, any>;
    }[];
  };
  kernel_events: {
    net: KernelEvent[];
    file: KernelEvent[];
    registry: KernelEvent[];
  };
}
