WITH normalized_raw AS (
  -- Step 1: Normalize the language-dependent columns first.
  -- 20250731 Revolut have changed export language from english to
  -- language of the region or country in which account is registered.
  SELECT
    -- Standardize the 'product' column
    CASE
      WHEN RAW.product = 'Giro' THEN 'Current'
      ELSE RAW.product
    END AS product,

    RAW.started, -- no change
    RAW.completed, -- no change

    -- Normalization for the 'type' column
    CASE
      WHEN RAW.type = 'Einzahlung' THEN 'TOPUP'
      WHEN RAW.type = 'Kartenbezahlung' THEN 'CARD_PAYMENT'
      WHEN RAW.type = 'Rückerstattung' THEN 'CARD_REFUND'
      WHEN RAW.type = 'Transfer' THEN 'TRANSFER'
      WHEN RAW.type = 'Umtausch' THEN 'EXCHANGE'
      --WHEN RAW.type = 'UNKNOWN' THEN 'FEE'
      --WHEN RAW.type = 'UNKNOWN' THEN 'ATM'
      -- Add all other German -> English mappings here
      ELSE RAW.type -- This keeps old data that is already in English
    END AS type,

    -- Normalization for the 'description' column
    CASE
      WHEN RAW.description LIKE 'Überweisung an %' THEN 'Transfer to Revolut user'
      WHEN RAW.description LIKE 'Überweisung von %' THEN 'Transfer from Revolut user'
      ELSE 
        REPLACE(
          REPLACE(RAW.description, 'Umgetauscht in ', 'Exchange to '),
        'Einzahlung von ', 'Top-Up by ') 
    END AS description,
    
    -- Keep all other columns from the raw table as they are
    RAW.amount, -- no change
    RAW.fee, -- no change
    RAW.currency, -- no change
    -- Standardize the 'state' column
    CASE
      WHEN RAW.state = 'ABGESCHLOSSEN' THEN 'COMPLETED'
      WHEN RAW.state = 'AUSSTEHEND' THEN 'PENDING'
      WHEN RAW.state = 'ABGELEHNT' THEN 'DECLINED'
      WHEN RAW.state = 'FEHLGESCHLAGEN' THEN 'FAILED'
      WHEN RAW.state = 'RÜCKGÄNGIG' THEN 'REVERTED'
      ELSE RAW.state
    END AS state,
    RAW.balance, -- no change
    RAW.account, -- no change
    RAW.month
  FROM
    `af-finanzen.banks.revolut_raw` AS RAW
)
-- Step 2: Now, calculate the fingerprint and add other columns based on the CLEAN, NORMALIZED data.
SELECT
  -- transaction id (tid) is now stable and language-independent!
  FARM_FINGERPRINT(
    CONCAT(
      -- not natural key IFNULL(N.type, ""),
      -- not natural key IFNULL(N.product, ""),
      IFNULL(N.started, DATE("1970-01-01")),
      IFNULL(N.completed, DATE("1970-01-01")),
      -- not natural key IFNULL(N.description, ""),
      IFNULL(N.amount, 0),
      IFNULL(N.fee, 0),
      IFNULL(N.currency, ""),
      -- not natural key IFNULL(N.state, ""),
      IFNULL(N.balance, 0),
      IFNULL(N.account, "")
    )
  ) AS tid,

  -- Select all the normalized columns
  N.type,
  N.product,
  N.started,
  N.completed,
  N.description,
  N.amount,
  N.fee,
  N.currency,
  N.state,
  N.balance,
  N.account,
  N.month,

  -- Your additional columns
  MIN(N.started) OVER (PARTITION BY N.description) AS first_started
FROM
  normalized_raw AS N
ORDER BY
  N.month DESC,
  N.started DESC;
