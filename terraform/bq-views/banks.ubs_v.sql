SELECT
    Kontonummer
  , Kartennummer
  , Inhaber
  , PARSE_DATE("%d.%m.%Y", Einkaufsdatum) Einkaufsdatum
  , Buchungstext
  , Branche
  , Betrag
  , Originalwaehrung
  , Kurs
  , Waehrung
  , Belastung
  , Gutschrift
  , PARSE_DATE("%d.%m.%Y", Buchung) Buchung
  , Monat
FROM banks.ubs