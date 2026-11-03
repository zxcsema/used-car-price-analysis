SELECT p0, n_per_group AS "n на группу", repeats AS "Повторений",
       seed, rejected AS "Ложных отклонений",
       rejection_rate AS "Частота", ci_lower AS "Wilson 95%: нижняя",
       ci_upper AS "Wilson 95%: верхняя", alpha
FROM sms_ab.sim_aa_summary;
