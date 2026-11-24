TABLES = {}

TABLES["users"] = (
    "CREATE TABLE IF NOT EXISTS users (\n"
    "  user_id       INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n"
    "  name          VARCHAR(80)  NOT NULL,\n"
    "  email         VARCHAR(255) NOT NULL UNIQUE,\n"
    "  password_hash VARCHAR(255) NOT NULL,\n"
    "  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP\n"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

TABLES["categories"] = (
    "CREATE TABLE IF NOT EXISTS categories (\n"
    "  category_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n"
    "  code          VARCHAR(32)  NOT NULL,\n"
    "  category_name VARCHAR(40)  NOT NULL,\n"
    "  kind          ENUM('expense','income') NOT NULL,\n"
    "  sort_order    SMALLINT     NOT NULL DEFAULT 0,\n"
    "  UNIQUE KEY uq_cat_code_kind (kind, code),\n"
    "  UNIQUE KEY uq_cat_id_kind   (category_id, kind)\n"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

TABLES["receipts"] = (
    "CREATE TABLE IF NOT EXISTS receipts (\n"
    "  receipt_id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n"
    "  user_id      INT UNSIGNED NOT NULL,\n"
    "  image_path   VARCHAR(255) NOT NULL,\n"
    "  uploaded_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
    "  read_status  ENUM('pending','processing','done','failed') NOT NULL DEFAULT 'pending',\n"
    "  discarded_at DATETIME     NULL,\n"
    "  extracted    JSON         NULL,\n"
    "  CONSTRAINT fk_rcpt_user FOREIGN KEY (user_id) REFERENCES users(user_id),\n"
    "  KEY idx_rcpt_queue (user_id, read_status, discarded_at, uploaded_at)\n"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

TABLES["commitments"] = (
    "CREATE TABLE IF NOT EXISTS commitments (\n"
    "  commitment_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n"
    "  user_id       INT UNSIGNED NOT NULL,\n"
    "  category_id   INT UNSIGNED NOT NULL,\n"
    "  kind          ENUM('bill','installment') NOT NULL,\n"
    "  title         VARCHAR(120) NOT NULL,\n"
    "  amount        INT UNSIGNED NOT NULL,\n"
    "  total_amount  INT UNSIGNED NULL,\n"
    "  months        TINYINT UNSIGNED NULL,\n"
    "  paid_count    TINYINT UNSIGNED NOT NULL DEFAULT 0,\n"
    "  due_day       TINYINT UNSIGNED NOT NULL,\n"
    "  start_date    DATE         NOT NULL,\n"
    "  next_due_date DATE         NOT NULL,\n"
    "  status        ENUM('active','done','canceled') NOT NULL DEFAULT 'active',\n"
    "  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
    "  CONSTRAINT fk_cmt_user FOREIGN KEY (user_id)     REFERENCES users(user_id),\n"
    "  CONSTRAINT fk_cmt_cat  FOREIGN KEY (category_id) REFERENCES categories(category_id),\n"
    "  CONSTRAINT ck_cmt_amount CHECK (amount > 0),\n"
    "  CONSTRAINT ck_cmt_due    CHECK (due_day BETWEEN 1 AND 31),\n"
    "  CONSTRAINT ck_cmt_months CHECK (months IS NULL OR (months BETWEEN 1 AND 24)),\n"
    "  CONSTRAINT ck_cmt_count  CHECK (kind = 'bill' OR months IS NULL OR paid_count <= months),\n"
    "  KEY idx_cmt_user_due (user_id, status, next_due_date)\n"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

TABLES["transactions"] = (
    "CREATE TABLE IF NOT EXISTS transactions (\n"
    "  txn_id        INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n"
    "  user_id       INT UNSIGNED NOT NULL,\n"
    "  kind          ENUM('expense','income') NOT NULL,\n"
    "  amount        INT UNSIGNED NOT NULL,\n"
    "  txn_date      DATE         NOT NULL,\n"
    "  category_id   INT UNSIGNED NOT NULL,\n"
    "  source        VARCHAR(120) NULL,\n"
    "  memo          VARCHAR(255) NULL,\n"
    "  receipt_id    INT UNSIGNED NULL,\n"
    "  commitment_id INT UNSIGNED NULL,\n"
    "  source_kind   ENUM('chat','photo','manual') NOT NULL,\n"
    "  deleted_at    DATETIME     NULL,\n"
    "  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
    "  updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\n"
    "  active_receipt_id INT UNSIGNED\n"
    "    GENERATED ALWAYS AS (IF(deleted_at IS NULL, receipt_id, NULL)) STORED,\n"
    "  CONSTRAINT fk_txn_user     FOREIGN KEY (user_id)       REFERENCES users(user_id),\n"
    "  CONSTRAINT fk_txn_cat_kind FOREIGN KEY (category_id, kind) REFERENCES categories(category_id, kind),\n"
    "  CONSTRAINT fk_txn_rcpt     FOREIGN KEY (receipt_id)    REFERENCES receipts(receipt_id),\n"
    "  CONSTRAINT fk_txn_cmt      FOREIGN KEY (commitment_id) REFERENCES commitments(commitment_id),\n"
    "  CONSTRAINT ck_txn_amount   CHECK (amount > 0),\n"
    "  UNIQUE KEY uq_txn_active_receipt (active_receipt_id),\n"
    "  KEY idx_txn_cat_kind  (category_id, kind),\n"
    "  KEY idx_txn_user_date (user_id, deleted_at, txn_date),\n"
    "  KEY idx_txn_user_cat  (user_id, deleted_at, category_id, txn_date),\n"
    "  KEY idx_txn_user_cmt  (user_id, commitment_id)\n"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

TABLES["chat_message"] = (
    "CREATE TABLE IF NOT EXISTS chat_message (\n"
    "  message_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n"
    "  user_id    INT UNSIGNED NOT NULL,\n"
    "  role       ENUM('user','assistant') NOT NULL,\n"
    "  body       TEXT         NOT NULL,\n"
    "  payload    JSON         NULL,\n"
    "  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
    "  CONSTRAINT fk_chat_user FOREIGN KEY (user_id) REFERENCES users(user_id),\n"
    "  KEY idx_chat_user (user_id, message_id)\n"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

TABLES["memory_fact"] = (
    "CREATE TABLE IF NOT EXISTS memory_fact (\n"
    "  fact_id    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,\n"
    "  user_id    INT UNSIGNED NOT NULL,\n"
    "  topic      VARCHAR(40)  NOT NULL,\n"
    "  value      VARCHAR(64)  NOT NULL,\n"
    "  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
    "  updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,\n"
    "  CONSTRAINT fk_fact_user FOREIGN KEY (user_id) REFERENCES users(user_id),\n"
    "  UNIQUE KEY uq_fact (user_id, topic)\n"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

TABLES["ai_usage"] = (
    "CREATE TABLE IF NOT EXISTS ai_usage (\n"
    "  user_id    INT UNSIGNED NOT NULL,\n"
    "  usage_date DATE         NOT NULL,\n"
    "  call_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,\n"
    "  PRIMARY KEY (user_id, usage_date),\n"
    "  CONSTRAINT fk_usage_user FOREIGN KEY (user_id) REFERENCES users(user_id)\n"
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
)

ORDER = [
    "users",
    "categories",
    "receipts",
    "commitments",
    "transactions",
    "chat_message",
    "memory_fact",
    "ai_usage",
]

SEED_CATEGORIES = [
    ("food", "食費", "expense", 10),
    ("transport", "交通費", "expense", 20),
    ("daily", "日用品", "expense", 30),
    ("social", "交際費", "expense", 40),
    ("utility", "光熱費", "expense", 50),
    ("other", "その他", "expense", 90),
    ("salary", "給与", "income", 10),
    ("support", "仕送り", "income", 20),
    ("other_income", "その他収入", "income", 90),
]


def apply_schema(cursor):
    for name in ORDER:
        cursor.execute(TABLES[name])
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()")
    present = {row[0] for row in cursor.fetchall()}
    missing = [name for name in ORDER if name not in present]
    if missing:
        raise RuntimeError("missing tables after apply: " + ", ".join(missing))
    return present


def seed_categories(cursor):
    sql = (
        "INSERT INTO categories (code, category_name, kind, sort_order) VALUES (%s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE category_name = VALUES(category_name), sort_order = VALUES(sort_order)"
    )
    for row in SEED_CATEGORIES:
        cursor.execute(sql, row)
    cursor.execute("SELECT kind, COUNT(*) FROM categories GROUP BY kind")
    return dict(cursor.fetchall())
