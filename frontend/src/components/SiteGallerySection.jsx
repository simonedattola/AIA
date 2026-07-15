import { useEffect, useState } from "react";
import { fetchGallery } from "../lib/api";
import GalleryCarousel from "./GalleryCarousel";

function shuffleImages(items) {
  const shuffled = [...items];
  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
}

export default function SiteGallerySection() {
  const [images, setImages] = useState([]);

  useEffect(() => {
    fetchGallery()
      .then((items) => setImages(shuffleImages(items)))
      .catch(() => setImages([]));
  }, []);

  if (!images.length) return null;
  return <GalleryCarousel images={images} />;
}
