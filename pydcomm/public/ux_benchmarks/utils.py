import tqdm
from pydcomm.public.ux_stats import ApiCallsRecorder


class Scenario(object):
    def __init__(self, stats=None, params=None, ret_vals=None, additionals=None, context=None):
        self.stats = stats if stats is not None else []
        self.params = params if params is not None else []
        self.ret_vals = ret_vals if ret_vals is not None else []
        self.additionals = additionals if additionals is not None else []
        self.context = context if context is not None else {}


def run_scenario(actions, initial_context=None):  # TBD flag for only parameters lengths?
    """

    :param dict initial_context: Dictionary of context
    :param list[(Scenario)->ActionResult] actions: Action to run.
    :return: Results of run.
    :rtype: dict
    """
    scenario = Scenario(context=initial_context)

    try:
        for api_action in tqdm.tqdm(actions):
            uxrecorder = ApiCallsRecorder()
            with uxrecorder:
                params, ret, context, additional, exception = api_action(scenario)

            for c in uxrecorder.api_stats:
                scenario.stats.append(c)
                scenario.params.append(params)
                scenario.ret_vals.append(ret)
                scenario.additionals.append(additional)
            scenario.context.update(context)
    finally:
        return dict(stats=scenario.stats,
                    params=scenario.params,
                    ret_vals=scenario.ret_vals,
                    additionals=scenario.additionals)
