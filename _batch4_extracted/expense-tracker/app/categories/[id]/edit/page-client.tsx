"use client";

import { SerializedCategory } from '@/lib/types';
import { updateCategory } from '../../actions';

export default function CategoryEditClient({ item }: { item: SerializedCategory }) {
  return (
    <form action={updateCategory.bind(null, item.id)}>
      <div>
        <label htmlFor="name">Nom de la catégorie</label>
        <input type="text" id="name" name="name" defaultValue={item.name} required />
      </div>
      <button type="submit">Mettre à jour</button>
    </form>
  );
}
