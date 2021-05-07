import { UIControl } from "./TaskInput";

export interface KernelEvent {
  event_name: string;
  params: Record<string, any>;
}

export interface NetworkEvent {
  event_name: string;
  params: {
    dip: string;
    sip: string;
    dport: number;
    sport: number;
    l4_proto: "tcp" | "udp";
    dport_name?: string;
    sport_name?: string;
    size?: number;
  };
}

export interface RegistryEvent {
  event_name: string;
  params: {
    key_name: string;
    status: string;

    // RegSetValue
    value?: string;
    type?: "REG_DWORD" | "REG_QWORD" | "REG_SZ" | "REG_EXPAND_SZ" | "REG_MULTI_SZ" | "REG_BINARY" | "UNKNOWN";
  };
}

export interface FileEvent {
  event_name: "CreateFile" | "ReadFile" | "WriteFile" | "DeleteFile" | "RenameFile" | "CloseFile" | "SetFileInformation" | "EnumDirectory";
  params: {
    file_object: string;
    file_name: string;
    irp: number;

    // Everything except EnumDirectory
    type?: "file" | "directory" | "pipe" | "console" | "other" | "unknown";

    // CreateFile
    operation?: "supersede" | "open" | "create" | "openif" | "overwrite" | "overwriteif";
    share_mask?: string;

    // WriteFile / ReadFile
    io_size?: number;
    offset?: number;

    // SetFileInformation
    class?: string;

    // EnumDirectory
    dir?: string;
  };
}

export interface WindowEnumeration {
  application_alive: boolean;
  program_installed: boolean;
  top_window_texts?: string[];
  base64_images?: string[];
  found_controls?: UIControl[];
}

export interface TaskOutput {
  _id: string;
  window_enumeration: WindowEnumeration;
  kernel_events: {
    net: NetworkEvent[];
    file: FileEvent[];
    registry: RegistryEvent[];
  };
  same_as?: string;
}
