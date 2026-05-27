"use client";

import { createCategory } from '../actions';

export default function CategoryCreateClient() {
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    await createCategory(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="name">Nom de la catégorie</label>
        <input type="text" id="name" name="name" required />
      </div>
      <button type="submit">Créer</button>
    </form>
  );
}
