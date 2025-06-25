import asn1tools

schema = asn1tools.compile_files("asn1_profile_schema.asn", "der")

def encode_profile(profile_data):
    return schema.encode("ProfilePackage", profile_data)
