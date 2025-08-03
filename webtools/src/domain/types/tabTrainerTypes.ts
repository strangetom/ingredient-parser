export type InputTrainer = {
  model: string;
  split: number;
  seed: number;
  html: boolean;
  detailed: boolean;
  confusion: boolean;
  sources: string[];
}
