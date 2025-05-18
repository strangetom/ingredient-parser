export const labellers = [
  "COMMENT",
  "B_NAME_TOK",
  "I_NAME_TOK",
  "NAME_VAR",
  "NAME_MOD",
  "NAME_SEP" ,
  "PREP",
  "PUNC",
  "PURPOSE",
  "QTY",
  "SIZE",
  "UNIT",
  "OTHER"
] as const;

export type LabellerCategory = typeof labellers[number];

export type Confidence = {
  confidence: number
  text: string
  starting_index: number
}

export type Amount = {
  APPROXIMATE: boolean
  MULTIPLIER: boolean
  RANGE: boolean
  SINGULAR: boolean
  quantity: number
  quantity_max: number
  unit: string
} & Confidence

export type FoundationFood = {
  fdc_id: string,
  category: string,
  data_type: string,
  url?: string
} & Omit<Confidence, 'starting_index'>

export type Marginals = Record<LabellerCategory, number>

export type Token = [
  string,
  LabellerCategory,
  Marginals | null
]
