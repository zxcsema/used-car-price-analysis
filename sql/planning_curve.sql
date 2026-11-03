SELECT delta_pp AS effect_pp, n_per_group,
       'p0=' || p0 || '; мощность=' || round((power * 100)::numeric) || '%' AS scenario
FROM sms_ab.planning_results
ORDER BY p0, power, delta_pp;
