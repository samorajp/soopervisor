"""
Loading dags
"""
from ploomber.constants import TaskStatus
from ploomber.spec import DAGSpec
from ploomber.exceptions import DAGSpecNotFound

from soopervisor.enum import Mode


def load_tasks(cmdr, name=None, mode='incremental'):
    """Load tasks names and their upstream dependencies

    Parameters
    ----------
    cmdr : Commander
        Commander instance used to print output

    name : str
        Target environment name. This prioritizes loading a
        pipeline.{name}.yaml spec, if such doesn't exist, it loads a
        pipeline.yaml

    mode : bool, default='incremental'
        One of 'incremental' (only include outdated tasks with respect to
        the remote metadata), 'regular' (ignore status, submit all tasks and
        determine status at runtime) or 'force' (ignore status, submit all
        tasks and force execution regardless of status)

    Returns
    -------
    task : dict
        A dictionary with tasks (keys) and upstream dependencies (values)
        to submit

    args : list
        A list of arguments to pass to "ploomber task {name}"
    """
    valid = Mode.get_values()

    if mode not in valid:
        raise ValueError(f'mode must be one of {valid!r}')

    try:
        spec = DAGSpec._find_relative(name=name)
    except DAGSpecNotFound:
        cmdr.print(f'No pipeline.{name}.yaml found, '
                   'looking for pipeline.yaml instead')
        spec = None

    if spec is None:
        spec = DAGSpec._find_relative()

    dag = spec.to_dag()

    if mode == 'incremental':
        dag.render(remote=True)

        tasks = []

        for name, task in dag.items():
            if not mode or task.exec_status != TaskStatus.Skipped:
                tasks.append(name)
    else:
        # force makes rendering faster. we just need this to ensure the
        # pipeline does not have any rendering problems before proceeding
        dag.render(force=True)

        tasks = list(dag.keys())

    out = {}

    for t in tasks:
        out[t] = [name for name in dag[t].upstream.keys() if name in tasks]

    args = [f'--entry-point {spec.path}']

    if mode == 'force':
        args.append('--force')

    return out, args
