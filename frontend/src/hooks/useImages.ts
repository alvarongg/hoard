import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { imagesApi } from "../services/imagesApi";
import type { ItemImage } from "../types/image";

function imagesKey(itemId: string) {
  return ["items", itemId, "images"] as const;
}

export function useImages(itemId: string) {
  const queryClient = useQueryClient();
  const key = imagesKey(itemId);

  const query = useQuery<ItemImage[], Error>({
    queryKey: key,
    queryFn: () => imagesApi.list(itemId),
    enabled: !!itemId,
  });

  const upload = useMutation<ItemImage, Error, File>({
    mutationFn: (file) => imagesApi.upload(itemId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  });

  const remove = useMutation<void, Error, string>({
    mutationFn: (imageId) => imagesApi.delete(imageId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: key }),
  });

  return { ...query, upload, remove };
}
