import py_sod_metrics
import os
from skimage import io
import torch
import numpy as np


# F-measure ↑ - 09CPVR
def maxfm(pred, gt):
    FM = py_sod_metrics.Fmeasure()
    FM.step(pred, gt)
    fm = FM.get_results()["fm"]
    return fm["curve"]


# Mean Absolute Error ↓ - 12CVPR
def mae(pred, gt):
    MAE = py_sod_metrics.MAE()
    MAE.step(pred, gt)
    mae = MAE.get_results()["mae"]
    return mae


# Weighted F-measure ↑ - 14CVPR
def wfm(pred, gt):
    WFM = py_sod_metrics.WeightedFmeasure()
    WFM.step(pred, gt)
    wfm = WFM.get_results()["wfm"]
    return wfm


# Structure-measure ↑ - 17ICCV
def sm(pred, gt):
    SM = py_sod_metrics.Smeasure()
    SM.step(pred, gt)
    sm = SM.get_results()["sm"]
    return sm


# Enhanced-measure ↑ - 18IJCAI
def em(pred, gt):
    EM = py_sod_metrics.Emeasure()
    EM.step(pred, gt)
    em = EM.get_results()["em"]
    # mean
    return em["curve"].mean()


# GTE
def mae_torch(pred, gt):
    h, w = gt.shape[0:2]
    sumError = torch.sum(torch.absolute(torch.sub(pred.float(), gt.float())))
    maeError = torch.divide(sumError, float(h) * float(w) * 255.0 + 1e-4)

    return maeError


def f1score_torch(pd, gt):
    # print(gt.shape)
    gtNum = torch.sum((gt > 128).float() * 1)  ## number of ground truth pixels

    pp = pd[gt > 128]
    nn = pd[gt <= 128]

    pp_hist = torch.histc(pp, bins=255, min=0, max=255)
    nn_hist = torch.histc(nn, bins=255, min=0, max=255)

    pp_hist_flip = torch.flipud(pp_hist)
    nn_hist_flip = torch.flipud(nn_hist)

    pp_hist_flip_cum = torch.cumsum(pp_hist_flip, dim=0)
    nn_hist_flip_cum = torch.cumsum(nn_hist_flip, dim=0)

    precision = (pp_hist_flip_cum) / (
        pp_hist_flip_cum + nn_hist_flip_cum + 1e-4
    )  # torch.divide(pp_hist_flip_cum,torch.sum(torch.sum(pp_hist_flip_cum, nn_hist_flip_cum), 1e-4))
    recall = (pp_hist_flip_cum) / (gtNum + 1e-4)
    f1 = (1 + 0.3) * precision * recall / (0.3 * precision + recall + 1e-4)

    return (
        torch.reshape(precision, (1, precision.shape[0])),
        torch.reshape(recall, (1, recall.shape[0])),
        torch.reshape(f1, (1, f1.shape[0])),
    )


def f1_mae_torch(pred, gt, valid_dataset, idx, mybins, hypar):
    import time

    tic = time.time()

    if len(gt.shape) > 2:
        gt = gt[:, :, 0]

    pre, rec, f1 = f1score_torch(pred, gt)
    mae = mae_torch(pred, gt)

    # hypar["valid_out_dir"] = hypar["valid_out_dir"]+"-eval" ###
    if hypar["valid_out_dir"] != "":
        if not os.path.exists(hypar["valid_out_dir"]):
            os.mkdir(hypar["valid_out_dir"])
        dataset_folder = os.path.join(
            hypar["valid_out_dir"], valid_dataset.dataset["data_name"][idx]
        )
        if not os.path.exists(dataset_folder):
            os.mkdir(dataset_folder)
        io.imsave(
            os.path.join(
                dataset_folder, valid_dataset.dataset["im_name"][idx] + ".png"
            ),
            pred.cpu().data.numpy().astype(np.uint8),
        )
    print(valid_dataset.dataset["im_name"][idx] + ".png")
    print("time for evaluation : ", time.time() - tic)

    return (
        pre.cpu().data.numpy(),
        rec.cpu().data.numpy(),
        f1.cpu().data.numpy(),
        mae.cpu().data.numpy(),
    )
