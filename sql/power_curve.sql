SELECT delta_pp AS effect_pp, empirical_power AS "Эмпирическая",
       analytical_power AS "Аналитическая", 0.80::float8 AS "Ориентир 80%"
FROM sms_ab.sim_power_results
ORDER BY delta_pp;
