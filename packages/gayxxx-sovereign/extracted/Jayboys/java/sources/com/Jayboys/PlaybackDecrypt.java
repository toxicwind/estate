package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000*\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010 \n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B\u0015\u0012\f\u0010\u0002\u001a\b\u0012\u0004\u0012\u00020\u00040\u0003¢\u0006\u0004\b\u0005\u0010\u0006J\u000f\u0010\t\u001a\b\u0012\u0004\u0012\u00020\u00040\u0003HÆ\u0003J\u0019\u0010\n\u001a\u00020\u00002\u000e\b\u0002\u0010\u0002\u001a\b\u0012\u0004\u0012\u00020\u00040\u0003HÆ\u0001J\u0014\u0010\u000b\u001a\u00020\f2\b\u0010\r\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\u000e\u001a\u00020\u000fHÖ\u0081\u0004J\n\u0010\u0010\u001a\u00020\u0011HÖ\u0081\u0004R\u0017\u0010\u0002\u001a\b\u0012\u0004\u0012\u00020\u00040\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0007\u0010\b¨\u0006\u0012"}, d2 = {"Lcom/Jayboys/PlaybackDecrypt;", "", "sources", "", "Lcom/Jayboys/PlaybackDecryptSource;", "<init>", "(Ljava/util/List;)V", "getSources", "()Ljava/util/List;", "component1", "copy", "equals", "", "other", "hashCode", "", "toString", "", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class PlaybackDecrypt {

    @org.jetbrains.annotations.NotNull
    private final java.util.List<com.Jayboys.PlaybackDecryptSource> sources;

    /* JADX WARN: Multi-variable type inference failed */
    public static /* synthetic */ com.Jayboys.PlaybackDecrypt copy$default(com.Jayboys.PlaybackDecrypt playbackDecrypt, java.util.List list, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            list = playbackDecrypt.sources;
        }
        return playbackDecrypt.copy(list);
    }

    @org.jetbrains.annotations.NotNull
    public final java.util.List<com.Jayboys.PlaybackDecryptSource> component1() {
        return this.sources;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Jayboys.PlaybackDecrypt copy(@org.jetbrains.annotations.NotNull java.util.List<com.Jayboys.PlaybackDecryptSource> sources) {
        return new com.Jayboys.PlaybackDecrypt(sources);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        return (other instanceof com.Jayboys.PlaybackDecrypt) && kotlin.jvm.internal.Intrinsics.areEqual(this.sources, ((com.Jayboys.PlaybackDecrypt) other).sources);
    }

    public int hashCode() {
        return this.sources.hashCode();
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "PlaybackDecrypt(sources=" + this.sources + ')';
    }

    public PlaybackDecrypt(@org.jetbrains.annotations.NotNull java.util.List<com.Jayboys.PlaybackDecryptSource> list) {
        this.sources = list;
    }

    @org.jetbrains.annotations.NotNull
    public final java.util.List<com.Jayboys.PlaybackDecryptSource> getSources() {
        return this.sources;
    }
}
