import torch
import torch.nn as nn


class NodeAttributeEncoder(nn.Module):
    """
    Learnable encoder for provenance graph node attributes (process names,
    file paths, IP addresses). Uses a shared token embedding table with
    node type embeddings, aggregated via masked mean pooling.

    Parameters
    ----------
    vocab_size : int
        Size of the token vocabulary (including <PAD>=0 and <UNK>=1).
    embed_dim : int
        Embedding dimension for tokens and node types.
    num_node_types : int
        Number of distinct node types (e.g., process, file, flow).
    output_dim : int
        Output dimension, should match the model's input feature dimension.
    max_path_tokens : int, optional
        Maximum number of tokens per node attribute. Default: ``8``.
    """

    def __init__(self, vocab_size, embed_dim, num_node_types, output_dim, max_path_tokens=8):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.type_embedding = nn.Embedding(num_node_types, embed_dim)
        self.projection = nn.Linear(embed_dim * 2, output_dim)
        self.max_path_tokens = max_path_tokens

    def forward(self, token_ids, token_lengths, node_types):
        """
        Parameters
        ----------
        token_ids : torch.LongTensor [N, max_path_tokens]
            Padded token IDs, 0 is padding.
        token_lengths : torch.LongTensor [N]
            Number of valid tokens per node.
        node_types : torch.LongTensor [N]
            Node type IDs (0=process, 1=file, 2=flow, ...).

        Returns
        -------
        out : torch.Tensor [N, output_dim]
        """
        attr_emb = self.token_embedding(token_ids)  # [N, max_tokens, embed_dim]
        mask = (token_ids != 0).unsqueeze(-1).float()  # [N, max_tokens, 1]
        attr_emb = (attr_emb * mask).sum(dim=1) / token_lengths.unsqueeze(-1).clamp(min=1).float()

        type_emb = self.type_embedding(node_types)  # [N, embed_dim]
        combined = torch.cat([attr_emb, type_emb], dim=-1)  # [N, embed_dim * 2]
        return self.projection(combined)
