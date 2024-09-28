# Training data

## Database

The training data is available in the `training.sqlite3` database in this directory. The database has a single table containing the training data.

The table schema is as follows:

| Field            | Type           | Description                                                  |
| ---------------- | -------------- | ------------------------------------------------------------ |
| id               | INTEGER        | Unique ID for sentence. This is the primary key for the table. |
| source           | TEXT           | String indicating the source of the sentence. One of `bbc`, `cookstr`, `nyt`. |
| sentence         | TEXT           | The input sentence.                                          |
| tokens           | JSON (TEXT)    | List of sentence tokens. This can be parsed using `json.loads`. |
| labels           | JSON (TEXT)    | List of labels for each sentence token. This can be parsed using `json.loads`. |
| foundation_foods | JSON (INTEGER) | List of indices of tokens that are foundation foods.         |

