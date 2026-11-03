SELECT delta_pp AS "Эффект, п.п.", empirical_power AS "Эмпирическая мощность",
       ci_lower AS "Wilson 95%: нижняя", ci_upper AS "Wilson 95%: верхняя",
       analytical_power AS "Аналитическая мощность", repeats AS "Повторений"
FROM sms_ab.sim_power_results
ORDER BY delta_pp;
