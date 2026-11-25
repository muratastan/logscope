-- Optional non-commercial plan seed. Does not create invoices, payments or outcomes.
BEGIN;
SET search_path TO logscope, public;
INSERT INTO product_plans(code,label,is_demo,monthly_price_minor,currency,feature_limits)
VALUES ('demo','Demo',TRUE,NULL,NULL,'{"data_mode":"synthetic"}'::jsonb),
       ('team','Team (concept)',FALSE,NULL,NULL,'{}'::jsonb),
       ('enterprise','Enterprise (concept)',FALSE,NULL,NULL,'{}'::jsonb)
ON CONFLICT(code) DO NOTHING;
COMMIT;
