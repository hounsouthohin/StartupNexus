import React from 'react';

const HomePage = () => {
  return (
    <div className="container mx-auto">
      <h1 className="text-4xl font-bold">Welcome to Todo Batch Alpha</h1>
      <p className="mt-4">Your one-stop solution for managing tasks efficiently.</p>
      <a href="/sign-in" className="mt-4 inline-block bg-blue-500 text-white px-4 py-2 rounded">Sign In</a>
      <a href="/sign-up" className="mt-4 inline-block bg-green-500 text-white px-4 py-2 rounded">Sign Up</a>
    </div>
  );
};

export default HomePage;