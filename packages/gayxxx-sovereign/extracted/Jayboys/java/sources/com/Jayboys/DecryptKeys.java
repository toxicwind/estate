package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000\"\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\u000e\n\u0002\b\r\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0002\b\u0086\b\u0018\u00002\u00020\u0001B%\u0012\b\b\u0001\u0010\u0002\u001a\u00020\u0003\u0012\b\b\u0001\u0010\u0004\u001a\u00020\u0003\u0012\b\b\u0001\u0010\u0005\u001a\u00020\u0003¢\u0006\u0004\b\u0006\u0010\u0007J\t\u0010\f\u001a\u00020\u0003HÆ\u0003J\t\u0010\r\u001a\u00020\u0003HÆ\u0003J\t\u0010\u000e\u001a\u00020\u0003HÆ\u0003J'\u0010\u000f\u001a\u00020\u00002\b\b\u0003\u0010\u0002\u001a\u00020\u00032\b\b\u0003\u0010\u0004\u001a\u00020\u00032\b\b\u0003\u0010\u0005\u001a\u00020\u0003HÆ\u0001J\u0014\u0010\u0010\u001a\u00020\u00112\b\u0010\u0012\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u0013\u001a\u00020\u0014HÖ\u0081\u0004J\n\u0010\u0015\u001a\u00020\u0003HÖ\u0081\u0004R\u0016\u0010\u0002\u001a\u00020\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\b\u0010\tR\u0016\u0010\u0004\u001a\u00020\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\n\u0010\tR\u0016\u0010\u0005\u001a\u00020\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u000b\u0010\t¨\u0006\u0016"}, d2 = {"Lcom/Jayboys/DecryptKeys;", "", "edge1", "", "edge2", "legacyFallback", "<init>", "(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V", "getEdge1", "()Ljava/lang/String;", "getEdge2", "getLegacyFallback", "component1", "component2", "component3", "copy", "equals", "", "other", "hashCode", "", "toString", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class DecryptKeys {

    @com.fasterxml.jackson.annotation.JsonProperty("edge_1")
    @org.jetbrains.annotations.NotNull
    private final java.lang.String edge1;

    @com.fasterxml.jackson.annotation.JsonProperty("edge_2")
    @org.jetbrains.annotations.NotNull
    private final java.lang.String edge2;

    @com.fasterxml.jackson.annotation.JsonProperty("legacy_fallback")
    @org.jetbrains.annotations.NotNull
    private final java.lang.String legacyFallback;

    public static /* synthetic */ com.Jayboys.DecryptKeys copy$default(com.Jayboys.DecryptKeys decryptKeys, java.lang.String str, java.lang.String str2, java.lang.String str3, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            str = decryptKeys.edge1;
        }
        if ((i & 2) != 0) {
            str2 = decryptKeys.edge2;
        }
        if ((i & 4) != 0) {
            str3 = decryptKeys.legacyFallback;
        }
        return decryptKeys.copy(str, str2, str3);
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final java.lang.String getEdge1() {
        return this.edge1;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component2, reason: from getter */
    public final java.lang.String getEdge2() {
        return this.edge2;
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component3, reason: from getter */
    public final java.lang.String getLegacyFallback() {
        return this.legacyFallback;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Jayboys.DecryptKeys copy(@com.fasterxml.jackson.annotation.JsonProperty("edge_1") @org.jetbrains.annotations.NotNull java.lang.String edge1, @com.fasterxml.jackson.annotation.JsonProperty("edge_2") @org.jetbrains.annotations.NotNull java.lang.String edge2, @com.fasterxml.jackson.annotation.JsonProperty("legacy_fallback") @org.jetbrains.annotations.NotNull java.lang.String legacyFallback) {
        return new com.Jayboys.DecryptKeys(edge1, edge2, legacyFallback);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof com.Jayboys.DecryptKeys)) {
            return false;
        }
        com.Jayboys.DecryptKeys decryptKeys = (com.Jayboys.DecryptKeys) other;
        return kotlin.jvm.internal.Intrinsics.areEqual(this.edge1, decryptKeys.edge1) && kotlin.jvm.internal.Intrinsics.areEqual(this.edge2, decryptKeys.edge2) && kotlin.jvm.internal.Intrinsics.areEqual(this.legacyFallback, decryptKeys.legacyFallback);
    }

    public int hashCode() {
        return (((this.edge1.hashCode() * 31) + this.edge2.hashCode()) * 31) + this.legacyFallback.hashCode();
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "DecryptKeys(edge1=" + this.edge1 + ", edge2=" + this.edge2 + ", legacyFallback=" + this.legacyFallback + ')';
    }

    public DecryptKeys(@com.fasterxml.jackson.annotation.JsonProperty("edge_1") @org.jetbrains.annotations.NotNull java.lang.String edge1, @com.fasterxml.jackson.annotation.JsonProperty("edge_2") @org.jetbrains.annotations.NotNull java.lang.String edge2, @com.fasterxml.jackson.annotation.JsonProperty("legacy_fallback") @org.jetbrains.annotations.NotNull java.lang.String legacyFallback) {
        this.edge1 = edge1;
        this.edge2 = edge2;
        this.legacyFallback = legacyFallback;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getEdge1() {
        return this.edge1;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getEdge2() {
        return this.edge2;
    }

    @org.jetbrains.annotations.NotNull
    public final java.lang.String getLegacyFallback() {
        return this.legacyFallback;
    }
}
