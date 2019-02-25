import functools
import os
from mpi4py import MPI
import numpy as np
from mpi4py_fft import PFFT, HDF5File, NCFile, newDarray, generate_xdmf

N = (12, 13, 14, 15)
comm = MPI.COMM_WORLD

ex = {True: 'c', False: 'r'}

writer = {'hdf5': functools.partial(HDF5File, mode='w'),
          'netcdf4': functools.partial(NCFile, mode='w')}
reader = {'hdf5': functools.partial(HDF5File, mode='r'),
          'netcdf4': functools.partial(NCFile, mode='r')}
ending = {'hdf5': '.h5', 'netcdf4': '.nc'}

def remove_if_exists(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

def test_2D(backend, forward_output):
    if backend == 'netcdf4':
        assert forward_output is False
    T = PFFT(comm, (N[0], N[1]))
    for i, domain in enumerate([None, ((0, np.pi), (0, 2*np.pi)),
                                (np.arange(N[0], dtype=np.float)*1*np.pi/N[0],
                                 np.arange(N[1], dtype=np.float)*2*np.pi/N[1])]):
        filename = "".join(('test2D_{}{}'.format(ex[i == 0], ex[forward_output]),
                            ending[backend]))
        if backend == 'netcdf4':
            remove_if_exists(filename)
        hfile = writer[backend](filename, T, domain=domain)
        assert hfile.backend() == backend
        u = newDarray(T, forward_output=forward_output, val=1)
        hfile.write(0, {'u': [u]}, forward_output=forward_output)
        hfile.write(1, {'u': [u]}, forward_output=forward_output)
        if not forward_output and backend == 'hdf5' and comm.Get_rank() == 0:
            generate_xdmf(filename)
            generate_xdmf(filename, order='visit')

        u0 = newDarray(T, forward_output=forward_output)
        read = reader[backend](filename, T)
        read.read(u0, 'u', step=0, forward_output=forward_output)
        assert np.allclose(u0, u)

def test_3D(backend, forward_output):
    if backend == 'netcdf4':
        assert forward_output is False
    T = PFFT(comm, (N[0], N[1], N[2]))
    d0 = ((0, np.pi), (0, 2*np.pi), (0, 3*np.pi))
    d1 = (np.arange(N[0], dtype=np.float)*1*np.pi/N[0],
          np.arange(N[1], dtype=np.float)*2*np.pi/N[1],
          np.arange(N[2], dtype=np.float)*3*np.pi/N[2])
    for i, domain in enumerate([None, d0, d1]):
        filename = ''.join(('test_{}{}'.format(ex[i == 0], ex[forward_output]),
                            ending[backend]))
        if backend == 'netcdf4':
            remove_if_exists('uv'+filename)
            remove_if_exists('v'+filename)

        h0file = writer[backend]('uv'+filename, T, domain)
        h1file = writer[backend]('v'+filename, T, domain)
        u = newDarray(T, forward_output=forward_output)
        v = newDarray(T, forward_output=forward_output)
        u[:] = np.random.random(u.shape)
        v[:] = 2
        for k in range(3):
            h0file.write(k, {'u': [u,
                                   (u, [slice(None), slice(None), 4]),
                                   (u, [5, 5, slice(None)])],
                             'v': [v,
                                   (v, [slice(None), 6, slice(None)])]},
                         forward_output=forward_output)
            h1file.write(k, {'v': [v,
                                   (v, [slice(None), 6, slice(None)]),
                                   (v, [6, 6, slice(None)])]},
                         forward_output=forward_output)
        # One more time with same k
        h0file.write(k, {'u': [u,
                               (u, [slice(None), slice(None), 4]),
                               (u, [5, 5, slice(None)])],
                         'v': [v,
                               (v, [slice(None), 6, slice(None)])]},
                     forward_output=forward_output)
        h1file.write(k, {'v': [v,
                               (v, [slice(None), 6, slice(None)]),
                               (v, [6, 6, slice(None)])]},
                     forward_output=forward_output)

        if not forward_output and backend == 'hdf5' and comm.Get_rank() == 0:
            generate_xdmf('uv'+filename)
            generate_xdmf('v'+filename, periodic=False)
            generate_xdmf('v'+filename, periodic=(True, True, True))
            generate_xdmf('v'+filename, order='visit')

        u0 = newDarray(T, forward_output=forward_output)
        read = reader[backend]('uv'+filename, T)
        read.read(u0, 'u', forward_output=forward_output, step=0)
        assert np.allclose(u0, u)
        read.read(u0, 'v', forward_output=forward_output, step=0)
        assert np.allclose(u0, v)

def test_4D(backend, forward_output):
    if backend == 'netcdf4':
        assert forward_output is False
    T = PFFT(comm, (N[0], N[1], N[2], N[3]))
    d0 = ((0, np.pi), (0, 2*np.pi), (0, 3*np.pi), (0, 4*np.pi))
    d1 = (np.arange(N[0], dtype=np.float)*1*np.pi/N[0],
          np.arange(N[1], dtype=np.float)*2*np.pi/N[1],
          np.arange(N[2], dtype=np.float)*3*np.pi/N[2],
          np.arange(N[3], dtype=np.float)*4*np.pi/N[3]
          )
    for i, domain in enumerate([None, d0, d1]):
        filename = "".join(('h5test4_{}{}'.format(ex[i == 0], ex[forward_output]),
                            ending[backend]))
        if backend == 'netcdf4':
            remove_if_exists('uv'+filename)
        h0file = writer[backend]('uv'+filename, T, domain)
        u = newDarray(T, forward_output=forward_output)
        v = newDarray(T, forward_output=forward_output)
        u[:] = np.random.random(u.shape)
        v[:] = 2
        for k in range(3):
            h0file.write(k, {'u': [u, (u, [slice(None), 4, slice(None), slice(None)])],
                             'v': [v, (v, [slice(None), slice(None), 5, 6])]},
                         forward_output=forward_output)

        if not forward_output and backend == 'hdf5' and comm.Get_rank() == 0:
            generate_xdmf('uv'+filename)

        u0 = newDarray(T, forward_output=forward_output)
        read = reader[backend]('uv'+filename, T)
        read.read(u0, 'u', forward_output=forward_output, step=0)
        assert np.allclose(u0, u)
        read.read(u0, 'v', forward_output=forward_output, step=0)
        assert np.allclose(u0, v)

if __name__ == '__main__':
    #pylint: disable=unused-import
    skip = {'hdf5': False, 'netcdf4': False}
    try:
        import h5py
    except ImportError:
        skip['hdf5'] = True
    try:
        import netCDF4
    except ImportError:
        skip['netcdf4'] = True
    for bnd in ('hdf5', 'netcdf4'):
        if not skip[bnd]:
            forw_output = [False]
            if bnd == 'hdf5':
                forw_output.append(True)
            for kind in forw_output:
                test_3D(bnd, kind)
                test_2D(bnd, kind)
                if bnd == 'hdf5':
                    test_4D(bnd, kind)
