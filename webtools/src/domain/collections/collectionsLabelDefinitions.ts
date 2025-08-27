import type { Token } from "../types";

export interface CollectionLabelDefinition {
  token: Token;
  definitions: string[];
}

export const collectionsLabelDefinitions: CollectionLabelDefinition[] = [
  {
    token: ["120", "QTY"],
    definitions: ["Quantity of the ingredient."],
  },
  {
    token: ["cup", "UNIT"],
    definitions: ["Unit of a quantity for the ingredient."],
  },
  {
    token: ["large", "SIZE"],
    definitions: [
      "Physical size of the ingredient (e.g. large, small). This is not used to label the size of the unit, these are given the UNIT label.",
    ],
  },
  {
    token: ["chopped", "PREP"],
    definitions: [
      "Preparation instructions for the ingredient (e.g. finely chopped).",
    ],
  },
  {
    token: ["for garnish", "PURPOSE"],
    definitions: ["Purpose of the ingredient (e.g. for garnish)"],
  },
  {
    token: ["!.?", "PUNC"],
    definitions: ["Any punctuation tokens."],
  },
  {
    token: ["fresh", "B_NAME_TOK"],
    definitions: ["The first token of an ingredient name."],
  },
  {
    token: ["squash", "I_NAME_TOK"],
    definitions: [
      "A token within an ingredient name that is not the first token.",
    ],
  },
  {
    token: ["chicken", "NAME_VAR"],
    definitions: [
      "A token that creates a variant of the ingredient name.",
      "This is used in cases such as beef or chicken stock. beef and chicken are labelled with NAME_VAR as they indicate variations of the ingredient name stock.",
    ],
  },
  {
    token: ["dried", "NAME_MOD"],
    definitions: [
      "A token that modifies multiple ingredient names in the sentence. For example in dried apples and pears, dried is labelled as NAME_MOD because it modifies the two ingredient names, apples and pears.",
    ],
  },
  {
    token: ["from bakery", "COMMENT"],
    definitions: [
      "Additional information in the sentence that does not fall in one of the other labels.",
    ],
  },
  {
    token: ["-----", "OTHER"],
    definitions: [
      "This label is used in sentences where the sentence normalisation and tokenization steps result in the incorrect tokens.",
      "This is rare in the training data (currently only 45 sentences) and sentences including this label are excluded when training and evaluating the model.",
      "The sentences are kept because the pre-processing steps should eventually handle them correctly.",
    ],
  },
];
