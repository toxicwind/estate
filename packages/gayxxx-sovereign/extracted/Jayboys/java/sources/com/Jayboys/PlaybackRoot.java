package com.Jayboys;

/* JADX INFO: compiled from: Extractors.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000&\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B\u000f\u0012\u0006\u0010\u0002\u001a\u00020\u0003¢\u0006\u0004\b\u0004\u0010\u0005J\t\u0010\b\u001a\u00020\u0003HÆ\u0003J\u0013\u0010\t\u001a\u00020\u00002\b\b\u0002\u0010\u0002\u001a\u00020\u0003HÆ\u0001J\u0014\u0010\n\u001a\u00020\u000b2\b\u0010\f\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\r\u001a\u00020\u000eHÖ\u0081\u0004J\n\u0010\u000f\u001a\u00020\u0010HÖ\u0081\u0004R\u0011\u0010\u0002\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007¨\u0006\u0011"}, d2 = {"Lcom/Jayboys/PlaybackRoot;", "", "playback", "Lcom/Jayboys/Playback;", "<init>", "(Lcom/Jayboys/Playback;)V", "getPlayback", "()Lcom/Jayboys/Playback;", "component1", "copy", "equals", "", "other", "hashCode", "", "toString", "", "Jayboys"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class PlaybackRoot {

    @org.jetbrains.annotations.NotNull
    private final com.Jayboys.Playback playback;

    public static /* synthetic */ com.Jayboys.PlaybackRoot copy$default(com.Jayboys.PlaybackRoot playbackRoot, com.Jayboys.Playback playback, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            playback = playbackRoot.playback;
        }
        return playbackRoot.copy(playback);
    }

    @org.jetbrains.annotations.NotNull
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final com.Jayboys.Playback getPlayback() {
        return this.playback;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Jayboys.PlaybackRoot copy(@org.jetbrains.annotations.NotNull com.Jayboys.Playback playback) {
        return new com.Jayboys.PlaybackRoot(playback);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        return (other instanceof com.Jayboys.PlaybackRoot) && kotlin.jvm.internal.Intrinsics.areEqual(this.playback, ((com.Jayboys.PlaybackRoot) other).playback);
    }

    public int hashCode() {
        return this.playback.hashCode();
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "PlaybackRoot(playback=" + this.playback + ')';
    }

    public PlaybackRoot(@org.jetbrains.annotations.NotNull com.Jayboys.Playback playback) {
        this.playback = playback;
    }

    @org.jetbrains.annotations.NotNull
    public final com.Jayboys.Playback getPlayback() {
        return this.playback;
    }
}
