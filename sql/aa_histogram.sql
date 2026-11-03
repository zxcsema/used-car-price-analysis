SELECT bin_center AS p_value, count AS "Симуляции",
       (SELECT repeats / 20.0 FROM sms_ab.sim_aa_summary) AS "Ожидание при равномерности"
FROM sms_ab.sim_aa_histogram
ORDER BY bin_center;
