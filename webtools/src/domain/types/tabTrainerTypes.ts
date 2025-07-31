export type InputTrainer = {
  model: string;
  split: number;
  html: boolean;
  detailed: boolean;
  confusion: boolean;
  sources: string[];
}
