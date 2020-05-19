import glac_mw.glac1d_toolbox as tb
import xarray as xr
import numpy as np
import numpy.ma as ma
import os
import datetime

# --------------------------------- #
# ---------- MAIN METHOD ---------- #
# --------------------------------- #

# To change for a new user
output_folder = "/nfs/annie/eeymr/work/outputs/proj_glac_mw"


def saving(discharge, ds_lsm, lsm_name, mode, start_year=-26, end_year=0, step=100, mode_smooth="diff"):
    print("__ Saving algorithm")
    
    lsm, longitude, latitude = ds_lsm.lsm.values, ds_lsm.longitude.values, ds_lsm.latitude.values
    
    folder_path, file_path, title, mode_tag = output_names(start_year, end_year, step, mode, mode_smooth, lsm_name)
    
    create_output_folder(folder_path)
    
    # m3/s to kg/m2/s
    processed_discharge = m3s_to_kgm2s(discharge, longitude, latitude)
    
    # masked array
    masked_discharge = masking_method(processed_discharge, lsm)
    
    # time
    time = np.arange(start_year * 1000, end_year * 1000 + step, step)
    
    ds = create_dataset(masked_discharge, time, longitude, latitude, title, start_year, end_year, step,
                        mode_tag, lsm_name)
    
    sav_path = f"{output_folder}/{folder_path}/{file_path}"
    print(f"__ Saving at: {sav_path}")
    ds.to_netcdf(sav_path)


def correcting_time(ds_ref, new_start_year, new_end_year, new_step):
    print("__ Correction algorithm")
    
    discharge_ref, longitude, latitude, t_ref = \
        ds_ref.discharge.values, ds_ref.longitude.values, ds_ref.latitude.values, ds_ref.t.values
    
    lsm_name = ds_ref.lsm
    mode_smooth = ds_ref.mode_smooth
    
    processed_time, processed_mw = process_time(discharge_ref, new_start_year, new_end_year, t_ref)
    
    if mode_smooth[-2] == "p":
        folder_path, file_path, title, mode_tag = output_names(new_start_year, new_end_year, new_step, "patched",
                                                               mode_smooth, lsm_name)
    elif mode_smooth[-2] == "s":
        folder_path, file_path, title, mode_tag = output_names(new_start_year, new_end_year, new_step, "spreaded",
                                                               mode_smooth, lsm_name)
    else:
        folder_path, file_path, title, mode_tag = output_names(new_start_year, new_end_year, new_step, "routed",
                                                               mode_smooth, lsm_name)
    
    create_output_folder(folder_path)
    
    ds = create_dataset(processed_mw, processed_time, longitude, latitude, title, new_start_year, new_end_year,
                        new_step, mode_tag, lsm_name)
    
    sav_path = f"{output_folder}/{folder_path}/{file_path}"
    print(f"__ Saving at: {sav_path}")
    ds.to_netcdf(sav_path)


# ------------------------------------ #
# ---------- SAVING METHODS ---------- #
# ------------------------------------ #

def create_output_folder(folder_name):
    dir_name = f"{output_folder}/{folder_name}"
    print("____ Creating directory at ", dir_name)    
    try:
        # Create target Directory
        os.mkdir(dir_name)
        print("____ Directory ", dir_name, " created.")
    except FileExistsError:
        print("____ Directory ", dir_name, " already exists.")


def create_dataset(discharge, time, longitude, latitude, title, start_year, end_year, step, mode_tag, lsm_name):
    ds = xr.Dataset({'discharge': (('t', 'latitude', 'longitude'), discharge)},
                    coords={'t': time, 'latitude': latitude,
                            'longitude': longitude})
    ds['discharge'].attrs['units'] = 'kg m-2 s-1'
    ds['discharge'].attrs['longname'] = 'P-E FLUX CORRECTION       KG/M2/S  A'
    
    ds['t'].attrs['long_name'] = 'time'
    ds['t'].attrs['units'] = 'years since 0000-01-01 00:00:00'
    ds['t'].attrs['calendar'] = '360_days'
    
    ds['longitude'].attrs['long_name'] = 'longitude'
    ds['longitude'].attrs['actual_range'] = '0., 359.'
    ds['longitude'].attrs['axis'] = 'X'
    ds['longitude'].attrs['units'] = 'degrees_east'
    ds['longitude'].attrs['modulo'] = '360'
    ds['longitude'].attrs['topology'] = 'circular'
    
    ds['latitude'].attrs['long_name'] = 'latitude'
    ds['latitude'].attrs['actual_range'] = '-89.5, 89.5'
    ds['latitude'].attrs['axis'] = 'y'
    ds['latitude'].attrs['units'] = 'degrees_north'
    
    ds.attrs['title'] = title
    ds.attrs['start_year'] = start_year
    ds.attrs['end_year'] = end_year
    ds.attrs['steps'] = step
    ds.attrs['processing'] = mode_tag
    ds.attrs['lsm'] = lsm_name
    ds.attrs['history'] = f"Created {datetime.datetime.now()} by Yvan Romé"
    
    return ds


def output_names(start_year, end_year, step, mode, mode_smooth, lsm_name):
    file_path = f"{lsm_name}.qrparm.glac_mw.nc"
    
    if mode == "routed":
        folder_path = f"wfix[{start_year}_{end_year}_{step}_{mode_smooth}]/"
        title = f"waterfix for transient GLAC1D last delgaciation HadCM3 simulations " \
                f"- {lsm_name} land sea mask - {start_year}kya to {end_year}kya with {step}yrs time step " \
                f"- {mode_smooth} mode processing - spreading applied but no patch correction."
        mode_tag = f"{mode_smooth}"
    elif mode == "spreaded":
        folder_path = f"wfix[{start_year}_{end_year}_{step}_{mode_smooth}_s]/"
        title = f"waterfix for transient GLAC1D last delgaciation HadCM3 simulations " \
                f"- {lsm_name} land sea mask - {start_year}kya to {end_year}kya with {step}yrs time step " \
                f"- {mode_smooth} mode processing - spreading applied but no patch correction."
        mode_tag = f"{mode_smooth}s"
    elif mode == "patched":
        folder_path = f"wfix[{start_year}_{end_year}_{step}_{mode_smooth}_sp]/"
        title = f"waterfix for transient GLAC1D last delgaciation HadCM3 simulations " \
                f"- {lsm_name} land sea mask - {start_year}kya to {end_year}kya with {step}yrs time step " \
                f"- {mode_smooth} mode processing - spreading and patch correction applied."
        mode_tag = f"{mode_smooth}sc"
    else:
        print("The mode wasn't recognized.")
        raise ValueError("Invalid mode.")
    
    return folder_path, file_path, title, mode_tag


def save_patched_waterfix(ds_wfix, patched_waterfix, expt_name, start_date, end_date):
    sav_path = \
        f"/nfs/annie/eeymr/work/outputs/Proj_GLAC1D/patched_waterfix/{expt_name}.qrparam.waterfix.hadcm3.patched.nc"
    print(f"____ Saving at: {sav_path}")
    
    longitude, latitude, t, depth = \
        ds_wfix.longitude.values, ds_wfix.latitude.values, ds_wfix.t.values, ds_wfix.depth.values
    
    # to netcdf
    ds = xr.Dataset({'field672': (('t', 'depth', 'latitude', 'longitude'), patched_waterfix)},
                    coords={'t': t, 'depth': depth, 'latitude': latitude, 'longitude': longitude})
    
    ds['t'].attrs['long_name'] = 'time'
    
    ds['depth'].attrs['long_name'] = 'depth'
    
    ds['field672'].attrs['units'] = 'kg m-2 s-1'
    ds['field672'].attrs['longname'] = 'P-E FLUX CORRECTION       KG/M2/S  A'
    
    ds['longitude'].attrs['long_name'] = 'longitude'
    ds['longitude'].attrs['actual_range'] = '0., 359.'
    ds['longitude'].attrs['axis'] = 'X'
    ds['longitude'].attrs['units'] = 'degrees_east'
    ds['longitude'].attrs['modulo'] = '360'
    ds['longitude'].attrs['topology'] = 'circular'
    
    ds['latitude'].attrs['long_name'] = 'latitude'
    ds['latitude'].attrs['actual_range'] = '-89.5, 89.5'
    ds['latitude'].attrs['axis'] = 'y'
    ds['latitude'].attrs['units'] = 'degrees_north'
    
    ds.attrs['title'] = \
        f"Corrected waterfix for {expt_name} based on the 21k experiment drift between {start_date} and {end_date}."
    ds.attrs['history'] = f"Created {datetime.datetime.now()} by Yvan Romé"
    
    ds.to_netcdf(sav_path)


# ---------------------------------------- #
# ---------- CONVERSION METHODS ---------- #
# ---------------------------------------- #

def masking_method(discharge, lsm):
    lsm_3d = np.resize(lsm, discharge.shape)
    return ma.array(discharge, mask=lsm_3d)


def m3s_to_kgm2s(discharge, lon, lat):
    d = 1000  # water density
    return np.divide(discharge * d, tb.surface_matrix(lon, lat))


def kgm2s_to_m3s(discharge, lon, lat):
    d = 1000  # water density
    return np.multiply(discharge / d, tb.surface_matrix(lon, lat))


# ---------------------------------------- #
# ---------- PROCESSING METHODS ---------- #
# ---------------------------------------- #

def process_time(discharge_ref, start, end, t_ref):
    start_k, end_k = start * 1000, end * 1000
    processed_time = np.arange(start_k, end_k + 100, 100)
    n_t, n_lat, n_lon = discharge_ref.shape
    discharge_processed = np.zeros((len(processed_time), n_lat, n_lon))
    
    if (start >= -26) and (end <= 0):
        id_start = np.where(t_ref == start_k)[0][0]
        id_end = np.where(t_ref == end_k)[0][0]
        
        discharge_processed[:] = discharge_ref[id_start:id_end + 1]
    
    elif (start < -26) and (end <= 0):
        id_26 = np.where(processed_time == -26000)[0][0]
        id_end = np.where(t_ref == end_k)[0][0]
        
        discharge_processed[:id_26] = discharge_ref[0]
        discharge_processed[id_26:] = discharge_ref[:id_end]
    
    elif (start >= -26) and (end > 0):
        id_start = np.where(t_ref == start_k)[0][0]
        id_0 = np.where(processed_time == 0)[0][0]
        
        discharge_processed[:id_0] = discharge_ref[id_start:]
        discharge_processed[id_0:] = discharge_ref[-1]
    
    elif (start < -26) and (end > 0):
        id_26 = np.where(processed_time == -26000)[0][0]
        id_0 = np.where(processed_time == 0)[0][0]
        
        discharge_processed[:id_26] = discharge_ref[0]
        discharge_processed[id_26: id_0 + 1] = discharge_ref[:]
        discharge_processed[id_0:] = discharge_ref[-1]
    
    else:
        raise ValueError("!!! Start or end paramters incorect")
    
    return discharge_processed, processed_time


# -------------------------------------------- #
# ---------- WATERFIX DRIFT METHODS ---------- #
# -------------------------------------------- #

def drift_waterfix_patch(path_ref, expt_name, ds_wfix, start_date, end_date):
    print(f"__ Computation of the waterfix patch")
    wfix = ds_wfix.field672.isel(depth=0).isel(t=0).values[:, :-2]
    srf_sal_flux = np.zeros(wfix.shape)
    
    for year in np.arange(start_date, end_date, 1):
        ds = xr.open_dataset(f'{path_ref}/{expt_name}o#pg00000{year}c1+.nc')
        srf_sal_flux += ds.srfSalFlux_ym_uo_1.isel(t=0).isel(unspecified=0).values - wfix
    
    return np.nanmean(srf_sal_flux / (end_date - start_date))


def patched_waterfix_patch(waterfix_patch, ds_lsm, ds_wfix):
    print(f"__ Creation of the patched waterfix file")
    longitude, latitude, lsm = ds_lsm.longitude.values, ds_lsm.latitude.values, ds_lsm.lsm.values
    
    wfix = ds_wfix.field672.values
    patched_waterfix = wfix
    patched_waterfix[0, 0, :, :-2] = (waterfix_patch * (1 - lsm)) + wfix[0, 0, :, :-2]
    
    return patched_waterfix
