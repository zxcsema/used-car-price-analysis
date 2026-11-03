SELECT p0, delta_pp AS "Эффект, п.п.", power AS "Мощность",
       n_per_group AS "n на группу", n_total AS "N всего",
       n_normal AS "n: нормальное приближение"
FROM sms_ab.planning_results
ORDER BY p0, delta_pp, power;
