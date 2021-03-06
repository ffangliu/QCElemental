import copy

import numpy as np

from ..exceptions import ValidationError
from ..physical_constants import constants
from ..util import unnp
from .to_string import formula_generator


def to_schema(molrec, dtype, units='Bohr', np_out=False):
    """Translate molparse internal Molecule spec into dictionary from other schemas.

    Parameters
    ----------
    molrec : dict
        Psi4 json Molecule spec.
    dtype : {'psi4', 1}
        Molecule schema format.
        ``1`` is https://molssi-qc-schema.readthedocs.io/en/latest/auto_topology.html V1 + #44 + #53
    units : {'Bohr', 'Angstrom'}
        Units in which to write string. There is not an option to write in
        intrinsic/input units. Some `dtype` may not allow all units.
    np_out : bool, optional
        When `True`, fields originating from geom, elea, elez, elem, mass, real, elbl will be ndarray.
        Use `False` to get a json-able version.
    #return_type : {'json', 'yaml'} Serialization format string to return.

    Returns
    -------
    qcschema : dict
        Dictionary of the `dtype` repr of `molrec`.

    """
    qcschema = {}

    if molrec['units'] == 'Angstrom' and units == 'Bohr' and 'input_units_to_au' in molrec:
        factor = molrec['input_units_to_au']
    else:
        factor = constants.conversion_factor(molrec['units'], units)
    geom = np.array(molrec['geom']) * factor
    nat = geom.shape[0] // 3

    name = molrec.get('name', formula_generator(molrec['elem']))
    #    tagline = """auto-generated by qcdb from molecule {}""".format(name)

    if dtype == 'psi4':
        if units not in ['Angstrom', 'Bohr']:
            raise ValidationError("""Psi4 Schema {} allows only 'Bohr'/'Angstrom' coordinates, not {}.""".format(
                dtype, units))
        qcschema = copy.deepcopy(molrec)
        qcschema['geom'] = geom
        qcschema['units'] = units
        qcschema['name'] = name

    elif dtype == 1:
        if units != 'Bohr':
            raise ValidationError("""QC_JSON_Schema {} allows only 'Bohr' coordinates, not {}.""".format(dtype, units))

        qcschema = {'schema_name': 'qc_schema_input', 'schema_version': 1, 'molecule': {}}

        qcschema['molecule']['symbols'] = np.array(molrec['elem'])
        qcschema['molecule']['geometry'] = geom
        qcschema['molecule']['masses'] = np.array(molrec['mass'])
        qcschema['molecule']['atomic_numbers'] = np.array(molrec['elez'])
        qcschema['molecule']['mass_numbers'] = np.array(molrec['elea'])
        qcschema['molecule']['atom_labels'] = np.array(molrec['elbl'])
        qcschema['molecule']['name'] = name
        if 'comment' in molrec:
            qcschema['molecule']['comment'] = molrec['comment']
        qcschema['molecule']['molecular_charge'] = molrec['molecular_charge']
        qcschema['molecule']['molecular_multiplicity'] = molrec['molecular_multiplicity']
        qcschema['molecule']['real'] = np.array(molrec['real'])
        fidx = np.split(np.arange(nat), molrec['fragment_separators'])
        qcschema['molecule']['fragments'] = [fr.tolist() for fr in fidx]
        qcschema['molecule']['fragment_charges'] = np.array(molrec['fragment_charges']).tolist()
        qcschema['molecule']['fragment_multiplicities'] = np.array(molrec['fragment_multiplicities']).tolist()
        qcschema['molecule']['fix_com'] = molrec['fix_com']
        qcschema['molecule']['fix_orientation'] = molrec['fix_orientation']
        if 'fix_symmetry' in molrec:
            qcschema['molecule']['fix_symmetry'] = molrec['fix_symmetry']
        qcschema['molecule']['provenance'] = copy.deepcopy(molrec['provenance'])
        if 'connectivity' in molrec:
            qcschema['molecule']['connectivity'] = copy.deepcopy(molrec['connectivity'])

    else:
        raise ValidationError("Schema dtype not understood, valid options are {{'psi4', 1}}. Found {}.".format(dtype))

    if not np_out:
        qcschema = unnp(qcschema)

    return qcschema

    #if return_type == 'json':
    #    return json.dumps(qcschema)
    #elif return_type == 'yaml':
    #    import yaml
    #    return yaml.dump(qcschema)
    #else:
    #    raise ValidationError("""Return type ({}) not recognized.""".format(return_type))
