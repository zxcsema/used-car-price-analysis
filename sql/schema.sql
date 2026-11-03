CREATE SCHEMA IF NOT EXISTS sms_ab;

CREATE TABLE IF NOT EXISTS sms_ab.experiment_users (
    client_id text PRIMARY KEY,
    treatment_flg smallint NOT NULL CHECK (treatment_flg IN (0, 1)),
    target smallint NOT NULL CHECK (target IN (0, 1))
);

CREATE TABLE IF NOT EXISTS sms_ab.experiment_summary (
    n_a bigint, n_b bigint, n_total bigint,
    buyers_a bigint, buyers_b bigint, buyers_total bigint,
    p_a double precision, p_b double precision,
    effect double precision, effect_pp double precision, relative_lift_pct double precision,
    z_stat double precision, p_value double precision,
    lower_one_sided95 double precision, ci_lower95 double precision, ci_upper95 double precision,
    alpha double precision, srm_stat double precision, srm_p_value double precision
);

CREATE TABLE IF NOT EXISTS sms_ab.planning_results (
    p0 double precision, delta double precision, delta_pp double precision,
    power double precision, n_per_group bigint, n_total bigint, n_normal bigint, alpha double precision
);

CREATE TABLE IF NOT EXISTS sms_ab.available_mde (
    p0 double precision, n_a bigint, n_b bigint, alpha double precision,
    power double precision, mde double precision, mde_pp double precision
);

CREATE TABLE IF NOT EXISTS sms_ab.sim_aa_summary (
    p0 double precision, n_per_group bigint, repeats integer, seed integer,
    alpha double precision, rejected integer, rejection_rate double precision,
    ci_lower double precision, ci_upper double precision
);

CREATE TABLE IF NOT EXISTS sms_ab.sim_aa_histogram (
    bin_left double precision, bin_right double precision,
    bin_center double precision, count integer
);

CREATE TABLE IF NOT EXISTS sms_ab.sim_power_results (
    p0 double precision, delta double precision, delta_pp double precision,
    n_per_group bigint, repeats integer, seed integer, alpha double precision,
    rejected integer, empirical_power double precision, ci_lower double precision,
    ci_upper double precision, analytical_power double precision
);
