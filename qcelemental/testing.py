import sys
import copy
import math
import pprint
import collections
import logging

import numpy as np

_logger = logging.Logger("TestLogger")


def get_logger():
    """
    Obtains the testing logger
    """
    return _logger


def _handle_return(passfail, label, message, return_message):
    """Function to print a '*label*...PASSED' line to log."""

    if passfail:
        _logger.info(f'    {label:.<66}PASSED')
    else:
        _logger.info(f'    {label:.<66}FAILED')
        _logger.info(f'    {message:.<66}')

    if return_message:
        return (passfail, message)
    else:
        return passfail


def compare_values(expected,
                   computed,
                   label=None,
                   *,
                   atol=1.e-8,
                   rtol=1.e-16,
                   equal_nan=False,
                   passnone=False,
                   return_message=False):
    """Returns True if two floats or float arrays are element-wise equal within a tolerance.

    Parameters
    ----------
    expected : float or float array-like
        Reference value against which `computed` is compared.
    computed : float or float array-like
        Input value to compare against `expected`.
    digits : int or float
        Absolute tolerance (see formula below), expressed as decimal digits for comparison.
        Values less than one are taken literally rather than as power.
        So `1` means `atol=0.1` and `2` means `atol=0.01` but `0.04` means `atol=0.04`
    label : str, optional
        Label for passed and error messages. Defaults to calling function name.
    rtol : float, optional
        Relative tolerance (see formula below). By default set to zero so `digits` dominates.
    equal_nan : bool, optional
        Passed to np.isclose.
    passnone : bool, optional
        Return True when both expected and computed are None.

    Returns
    -------
    allclose : bool
        Returns True if `expected` and `computed` are equal within tolerance; False otherwise.
    message : str, optional
        When return_message=True, also return passed or error message.

    Notes
    -----
    Akin to np.allclose.
    Sets rtol to zero to match expected Psi4 behaviour, otherwise measured as:
        absolute(computed - expected) <= (atol + rtol * absolute(expected))

    """
    label = label or sys._getframe().f_back.f_code.co_name
    pass_message = f'\t{label:.<66}PASSED'

    if passnone:
        if expected is None and computed is None:
            return _handle_return(True, label, pass_message, return_message)

    try:
        xptd, cptd = np.array(expected, dtype=np.float), np.array(computed, dtype=np.float)
    except Exception:
        return _handle_return(False, label, f"""\t{label}: inputs not cast-able to ndarray of np.float.""",
                              return_message)

    if xptd.shape != cptd.shape:
        return _handle_return(False, label,
                              f"""\t{label}: computed shape ({cptd.shape}) does not match ({xptd.shape}).""",
                              return_message)

    # digits_str = f'to atol={atol} and rtol={rtol}'
    digits1 = abs(int(np.log10(atol)))
    digits_str = f"to {digits1} digits"
    digits1 += 1

    isclose = np.isclose(cptd, xptd, rtol=rtol, atol=atol, equal_nan=equal_nan)
    allclose = bool(np.all(isclose))

    if allclose:
        message = pass_message

    else:
        if xptd.shape == ():
            xptd_str = f'{xptd:.{digits1}f}'
        else:
            xptd_str = np.array_str(xptd, max_line_width=120, precision=12, suppress_small=True)
            xptd_str = '\n'.join('    ' + ln for ln in xptd_str.splitlines())

        if cptd.shape == ():
            cptd_str = f'{cptd:.{digits1}f}'
        else:
            cptd_str = np.array_str(cptd, max_line_width=120, precision=12, suppress_small=True)
            cptd_str = '\n'.join('    ' + ln for ln in cptd_str.splitlines())

        diff = cptd - xptd
        if xptd.shape == ():
            diff_str = f'{diff:.{digits1}f}'
            message = """\t{}: computed value ({}) does not match ({}) {} by difference ({}).""".format(
                label, cptd_str, xptd_str, digits_str, diff_str)
        else:
            diff[isclose] = 0.0
            diff_str = np.array_str(diff, max_line_width=120, precision=12, suppress_small=False)
            diff_str = '\n'.join('    ' + ln for ln in diff_str.splitlines())
            message = """\t{}: computed value does not match {}.\n  Expected:\n{}\n  Observed:\n{}\n  Difference (passed elements are zeroed):\n{}\n""".format(
                label, digits_str, xptd_str, cptd_str, diff_str)

    return _handle_return(allclose, label, message, return_message)


def compare(expected, computed, label=None, *, return_message=False):
    """Returns True if two floats or float arrays are element-wise equal within a tolerance.

    Parameters
    ----------
    expected : float or float array-like
        Reference value against which `computed` is compared.
    computed : float or float array-like
        Input value to compare against `expected`.
    label : str, optional
        Label for passed and error messages. Defaults to calling function name.

    Returns
    -------
    allclose : bool
        Returns True if `expected` and `computed` are equal; False otherwise.
    message : str, optional
        When return_message=True, also return passed or error message.

    Notes
    -----
    Akin to np.array_equal.

    """
    label = label or sys._getframe().f_back.f_code.co_name
    pass_message = f'\t{label:.<66}PASSED'

    try:
        xptd, cptd = np.array(expected), np.array(computed)
    except Exception:
        return _handle_return(False, label, f"""\t{label}: inputs not cast-able to ndarray.""", return_message)

    if xptd.shape != cptd.shape:
        return _handle_return(False, label,
                              f"""\t{label}: computed shape ({cptd.shape}) does not match ({xptd.shape}).""",
                              return_message)

    isclose = np.asarray(xptd == cptd)
    allclose = bool(isclose.all())

    if allclose:
        message = pass_message

    else:
        if xptd.shape == ():
            xptd_str = f'{xptd}'
        else:
            xptd_str = np.array_str(xptd, max_line_width=120, precision=12, suppress_small=True)
            xptd_str = '\n'.join('    ' + ln for ln in xptd_str.splitlines())

        if cptd.shape == ():
            cptd_str = f'{cptd}'
        else:
            cptd_str = np.array_str(cptd, max_line_width=120, precision=12, suppress_small=True)
            cptd_str = '\n'.join('    ' + ln for ln in cptd_str.splitlines())

        try:
            diff = cptd - xptd
        except TypeError:
            diff_str = '(n/a)'
        else:
            if xptd.shape == ():
                diff_str = f'{diff}'
            else:
                diff_str = np.array_str(diff, max_line_width=120, precision=12, suppress_small=False)
                diff_str = '\n'.join('    ' + ln for ln in diff_str.splitlines())

        if xptd.shape == ():
            message = """\t{}: computed value ({}) does not match ({}) by difference ({}).""".format(
                label, cptd_str, xptd_str, diff_str)
        else:
            message = """\t{}: computed value does not match.\n  Expected:\n{}\n  Observed:\n{}\n  Difference:\n{}\n""".format(
                label, xptd_str, cptd_str, diff_str)

    return _handle_return(allclose, label, message, return_message)


def _compare_recursive(expected, computed, atol, rtol, _prefix=False):

    errors = []
    name = _prefix or "root"
    prefix = name + "."

    if isinstance(expected, (str, int, bool)):
        if expected != computed:
            errors.append((name, "Value {} did not match {}.".format(expected, computed)))

    elif isinstance(expected, (list, tuple)):
        if len(expected) != len(computed):
            errors.append((name, "Iterable lengths did not match"))
        else:
            for i, item1, item2 in zip(range(len(expected)), expected, computed):
                errors.extend(_compare_recursive(item1, item2, _prefix=prefix + str(i), atol=atol, rtol=rtol))

    elif isinstance(expected, dict):

        expected_extra = computed.keys() - expected.keys()
        computed_extra = expected.keys() - computed.keys()
        if len(expected_extra):
            errors.append((name, "Found extra keys {}".format(expected_extra)))
        if len(computed_extra):
            errors.append((name, "Missing keys {}".format(computed_extra)))

        for k in expected.keys() & computed.keys():
            name = prefix + str(k)
            errors.extend(_compare_recursive(expected[k], computed[k], _prefix=name, atol=atol, rtol=rtol))
    elif isinstance(expected, (np.ndarray, float)):
        if np.allclose(expected, computed, atol=atol, rtol=rtol) is False:
            errors.append((name, "Arrays are not close."))
    elif isinstance(expected, type(None)):
        if expected is not computed:
            errors.append((name, "'None' does not match."))

    else:
        errors.append((name, "Type {} not understood stopping recursive compare.".format(type(expected))))

    return errors


def compare_recursive(expected, computed, label=None, *, atol=1.e-8, rtol=1.e-5, return_message=False):

    label = label or sys._getframe().f_back.f_code.co_name

    errors = _compare_recursive(expected, computed, atol=atol, rtol=rtol)

    message = []
    for e in errors:
        message.append(e[0])
        message.append("    " + e[1])

    message = "\n".join(message)

    return _handle_return(len(message) == 0, label, message, return_message)


def compare_molrecs(expected, computed, label, *, tolforgive=None, verbose=1, relative_geoms='exact'):
    """Function to compare Molecule dictionaries. Prints
#    :py:func:`util.success` when elements of `computed` match elements of
#    `expected` to `tol` number of digits (for float arrays).

    """
    thresh = 10**-tol if tol >= 1 else tol

    # Need to manipulate the dictionaries a bit, so hold values
    xptd = copy.deepcopy(expected)
    cptd = copy.deepcopy(computed)

    def massage_dicts(dicary):
        # deepdiff can't cope with np.int type
        #   https://github.com/seperman/deepdiff/issues/97
        if 'elez' in dicary:
            dicary['elez'] = [int(z) for z in dicary['elez']]
        if 'elea' in dicary:
            dicary['elea'] = [int(a) for a in dicary['elea']]
        # deepdiff w/py27 complains about unicode type and val errors
        if 'elem' in dicary:
            dicary['elem'] = [str(e) for e in dicary['elem']]
        if 'elbl' in dicary:
            dicary['elbl'] = [str(l) for l in dicary['elbl']]
        if 'fix_symmetry' in dicary:
            dicary['fix_symmetry'] = str(dicary['fix_symmetry'])
        if 'units' in dicary:
            dicary['units'] = str(dicary['units'])
        if 'fragment_files' in dicary:
            dicary['fragment_files'] = [str(f) for f in dicary['fragment_files']]
        # and about int vs long errors
        if 'molecular_multiplicity' in dicary:
            dicary['molecular_multiplicity'] = int(dicary['molecular_multiplicity'])
        if 'fragment_multiplicities' in dicary:
            dicary['fragment_multiplicities'] = [(m if m is None else int(m))
                                                 for m in dicary['fragment_multiplicities']]
        if 'fragment_separators' in dicary:
            dicary['fragment_separators'] = [(s if s is None else int(s)) for s in dicary['fragment_separators']]
        # forgive generator version changes
        if 'provenance' in dicary:
            dicary['provenance'].pop('version')
        # regularize connectivity ordering
        if 'connectivity' in dicary:
            conn = [(min(at1, at2), max(at1, at2), bo) for (at1, at2, bo) in dicary['connectivity']]
            conn.sort(key=lambda tup: tup[0])
            dicary['connectivity'] = conn

        return dicary

    xptd = massage_dicts(xptd)
    cptd = massage_dicts(cptd)

    if relative_geoms == 'exact':
        pass
    elif relative_geoms == 'align':
        raise FeatureNotImplemented(
            """compare_molrecs(..., relative_geoms='align') not available without B787 from qcdb.""")
        ## can't just expect geometries to match, so we'll align them, check that
        ##   they overlap and that the translation/rotation arrays jibe with
        ##   fix_com/orientation, then attach the oriented geom to computed before the
        ##   recursive dict comparison.
        #from .align import B787
        #cgeom = np.array(cptd['geom']).reshape((-1, 3))
        #rgeom = np.array(xptd['geom']).reshape((-1, 3))
        #rmsd, mill = B787(rgeom=rgeom,
        #                  cgeom=cgeom,
        #                  runiq=None,
        #                  cuniq=None,
        #                  atoms_map=True,
        #                  mols_align=True,
        #                  run_mirror=False,
        #                  verbose=0)
        #if cptd['fix_com']:
        #    compare_integers(1, np.allclose(np.zeros((3)), mill.shift, atol=thresh), 'null shift', verbose=verbose)
        #if cptd['fix_orientation']:
        #    compare_integers(1, np.allclose(np.identity(3), mill.rotation, atol=thresh), 'null rotation', verbose=verbose)
        #ageom = mill.align_coordinates(cgeom)
        #cptd['geom'] = ageom.reshape((-1))

    compare_recursive(xptd, cptd, tol, label, forgive=forgive, verbose=verbose)
