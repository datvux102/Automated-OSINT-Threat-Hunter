export interface CollectPayload {
  source: string;
  query: string;
}

export interface CollectRecord {
  source: string;
  query: string;
  raw_text: string;
}

export interface CollectResponse {
  ok: boolean;
  record: CollectRecord;
}
