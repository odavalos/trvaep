import numpy as np
import scanpy as sc

from trvae_pyt.model import CVAE
from trvae_pyt.model import Trainer

adata = sc.read("../data/kang_seurat.h5ad")
sc.pp.normalize_per_cell(adata)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata, n_top_genes=3000)
adata = adata[:, adata.var['highly_variable']]
n_conditions = adata.obs["condition"].unique().shape[0]
adata_train = adata[~((adata.obs["cell_type"] == "pDC")
                      & (adata.obs["condition"] == "CTRL"))]
model = CVAE(adata_train.n_vars, num_classes=n_conditions,
             encoder_layer_sizes=[128, 64, 32], decoder_layer_sizes=[32, 64, 128], latent_dim=10, alpha=0.0001,
             use_mmd=True, beta=10)
trainer = Trainer(model, adata_train)
trainer.train_trvae(100, 64, early_patience=20)
latent_y = model.get_y(adata.X.A, model.label_encoder.transform(adata.obs["condition"]))
adata_latent = sc.AnnData(latent_y)
adata_latent.obs["cell_type"] = adata.obs["cell_type"].tolist()
adata_latent.obs["condition"] = adata.obs["condition"].tolist()
sc.pp.neighbors(adata_latent)
sc.tl.umap(adata_latent)
sc.pl.umap(adata_latent, color=["condition", "cell_type"])
data = model.get_latent(adata.X.A, model.label_encoder.transform(adata.obs["condition"]))
adata_latent = sc.AnnData(data)
adata_latent.obs["cell_type"] = adata.obs["cell_type"].tolist()
adata_latent.obs["condition"] = adata.obs["condition"].tolist()
sc.pp.neighbors(adata_latent)
sc.tl.umap(adata_latent)
sc.pl.umap(adata_latent, color=["condition", "cell_type"])
ground_truth = adata_source = adata[(adata.obs["cell_type"] == "pDC")]
adata_source = adata[(adata.obs["cell_type"] == "pDC") & (adata.obs["condition"] == "CTRL")]
predicted_data = model.predict(x=adata_source.X.A, y=adata_source.obs["condition"].tolist(),
                               target="STIM")
adata_pred = sc.AnnData(predicted_data)
adata_pred.obs["condition"] = np.tile("predicted", len(adata_pred))
adata_pred.var_names = adata_source.var_names.tolist()
all_adata = ground_truth.concatenate(adata_pred)
sc.tl.pca(all_adata)
sc.pl.pca(all_adata, color=["condition"])
sc.pl.violin(all_adata, keys="ISG15", groupby="condition")
