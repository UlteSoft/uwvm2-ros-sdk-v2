struct owns_lifetime {
    unsigned payload;
    ~owns_lifetime();
};

unsigned sample() return_failure{owns_lifetime};
